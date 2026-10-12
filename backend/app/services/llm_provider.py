"""Camada de IA opcional. Configurada só por variáveis de ambiente; sem ela, tudo roda por regras.

Variáveis:
  LLM_PROVIDER  none | openai | anthropic   (openai = qualquer API compatível: OpenAI, OpenRouter, Groq, Ollama...)
  LLM_API_KEY   chave (opcional para servidores locais, como Ollama)
  LLM_MODEL     nome do modelo
  LLM_BASE_URL  opcional; ex.: http://localhost:11434/v1 (Ollama)
  LLM_TIMEOUT   segundos (padrão 60)
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass

import httpx

from app.models.schemas import AppStatus, ParsedJob, Profile
from app.services.catalog import CATALOG, canonical, find_terms

log = logging.getLogger("jobagent.llm")  # nunca registrar chaves ou texto de perfil/vaga

DEFAULT_URLS = {"openai": "https://api.openai.com/v1", "anthropic": "https://api.anthropic.com/v1"}


class LLMError(RuntimeError):
    pass


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    model: str
    base_url: str
    timeout: float

    @property
    def enabled(self) -> bool:
        if self.provider not in ("openai", "anthropic") or not self.model:
            return False
        local = any(h in self.base_url for h in ("localhost", "127.0.0.1"))
        return bool(self.api_key) or local


def load_config() -> LLMConfig:
    provider = os.environ.get("LLM_PROVIDER", "none").strip().lower()
    return LLMConfig(
        provider=provider,
        api_key=os.environ.get("LLM_API_KEY", "").strip(),
        model=os.environ.get("LLM_MODEL", "").strip(),
        base_url=(os.environ.get("LLM_BASE_URL", "").strip() or DEFAULT_URLS.get(provider, "")).rstrip("/"),
        timeout=float(os.environ.get("LLM_TIMEOUT", "60") or 60),
    )


def get_status() -> AppStatus:
    cfg = load_config()
    if cfg.enabled:
        return AppStatus(ai_enabled=True, provider=cfg.provider, model=cfg.model, mode="llm",
                         message=f"IA ativa ({cfg.provider}, modelo {cfg.model}). Em caso de falha, o sistema volta ao modo por regras.")
    return AppStatus(
        ai_enabled=False, provider="none", model="", mode="rules",
        message="Modo sem IA (regras e templates): a extração reconhece apenas termos de um catálogo fixo e o texto do "
                "currículo vem de modelos. Configure LLM_PROVIDER no arquivo .env para ativar a IA.",
    )


def complete_json(system: str, user: str, cfg: LLMConfig | None = None) -> dict:
    cfg = cfg or load_config()
    if not cfg.enabled:
        raise LLMError("IA não configurada.")
    try:
        if cfg.provider == "anthropic":
            r = httpx.post(
                f"{cfg.base_url}/messages",
                headers={"x-api-key": cfg.api_key, "anthropic-version": "2023-06-01"},
                json={"model": cfg.model, "max_tokens": 2500, "system": system,
                      "messages": [{"role": "user", "content": user}]},
                timeout=cfg.timeout,
            )
            r.raise_for_status()
            text = "".join(b.get("text", "") for b in r.json().get("content", []))
        else:
            headers = {"Authorization": f"Bearer {cfg.api_key}"} if cfg.api_key else {}
            r = httpx.post(
                f"{cfg.base_url}/chat/completions", headers=headers,
                json={"model": cfg.model, "temperature": 0.2,
                      "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                timeout=cfg.timeout,
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise LLMError(f"Falha ao chamar o provedor de IA ({type(exc).__name__}).") from exc
    return _extract_json(text)


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise LLMError("A resposta da IA não continha JSON.")
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise LLMError("A resposta da IA não era um JSON válido.") from exc
    if not isinstance(data, dict):
        raise LLMError("A resposta da IA tinha formato inesperado.")
    return data


# ------------------------------------------------------------------ Extração da vaga
PARSE_SYSTEM = (
    "Você extrai dados estruturados de vagas de emprego. Responda SOMENTE com um objeto JSON. "
    "Use apenas informações presentes no texto; se algo não estiver explícito, use string vazia ou lista vazia. "
    "Chaves: title, company, seniority (Estágio|Trainee|Júnior|Pleno|Sênior|Especialista|''), responsibilities[], "
    "required[], desired[], technologies_required[], technologies_desired[], soft_skills[], keywords[], "
    "years_required (inteiro ou null). Em technologies_* e keywords liste apenas termos que aparecem literalmente na vaga."
)


def _str_list(v, limit: int = 20) -> list[str]:
    return [str(x).strip()[:300] for x in v if str(x).strip()][:limit] if isinstance(v, list) else []


def _literal_terms(items: list[str], text: str) -> list[str]:
    low = text.lower()
    return [t for t in items if t.lower() in low]


def enhance_parse(job_text: str, rules: ParsedJob) -> ParsedJob:
    """Mescla a extração da IA com a de regras, descartando termos que não estão no texto da vaga."""
    data = complete_json(PARSE_SYSTEM, f"VAGA:\n{job_text[:12000]}")
    out = rules.model_copy(deep=True)
    for field in ("title", "company", "seniority"):
        v = str(data.get(field) or "").strip()[:120]
        if v and not getattr(out, field):
            setattr(out, field, v)
    for field in ("responsibilities", "required", "desired", "soft_skills"):
        v = _str_list(data.get(field))
        if v:
            setattr(out, field, v)
    for field in ("technologies_required", "technologies_desired", "keywords"):
        extra = _literal_terms(_str_list(data.get(field), 40), job_text)
        merged = list(getattr(out, field))
        known = {canonical(m).lower() for m in merged}
        for t in extra:
            if canonical(t).lower() not in known:
                merged.append(t)
                known.add(canonical(t).lower())
        setattr(out, field, merged)
    # um termo obrigatório não pode ficar duplicado como desejável
    req = {t.lower() for t in out.technologies_required}
    out.technologies_desired = [t for t in out.technologies_desired if t.lower() not in req]
    yrs = data.get("years_required")
    if out.years_required is None and isinstance(yrs, int) and 0 < yrs < 30:
        out.years_required = yrs
    return out


# ------------------------------------------------------------------ Texto do currículo
RESUME_SYSTEM = (
    "Você redige textos de currículo em português do Brasil, objetivos e compatíveis com ATS. "
    "Use EXCLUSIVAMENTE os fatos do PERFIL fornecido. Proibido: inventar empresas, cargos, métricas, números, "
    "anos de experiência ou tecnologias que não estejam no perfil. Projetos acadêmicos/portfólio não são empregos. "
    "Responda SOMENTE com JSON: {\"title\": string (até 60 caracteres, sem senioridade), "
    "\"summary\": string (3 a 4 frases, sem primeira pessoa)}."
)


def profile_facts(profile: Profile, allowed_terms: list[str]) -> str:
    facts = {
        "formacao": [f"{e.course} - {e.institution} ({e.period})" for e in profile.education],
        "conquistas": profile.achievements,
        "certificacoes": [c.name for c in profile.certifications],
        "competencias": {c.name: c.items for c in profile.skills},
        "projetos": [{"nome": p.name, "descricao": p.description, "tecnologias": p.technologies} for p in profile.projects],
        "experiencias_profissionais": [f"{x.role} - {x.company}" for x in profile.experiences] or "NENHUMA CADASTRADA",
        "termos_da_vaga_com_respaldo": allowed_terms,
    }
    return json.dumps(facts, ensure_ascii=False)


FORBIDDEN = re.compile(r"\d+\s*\+?\s*(anos|years)|\d+\s*%|\b(milh|mil )\w*|\$\s*\d|R\$", re.I)


def validate_generated_text(text: str, supported_terms: set[str], has_experience: bool) -> str | None:
    """Devolve o motivo da rejeição, ou None se o texto é aceitável."""
    if FORBIDDEN.search(text):
        return "contém números/métricas não respaldados"
    unsupported = [t for t in find_terms(text) if t not in supported_terms and t in CATALOG]
    if unsupported:
        return f"menciona tecnologias sem respaldo no perfil ({', '.join(unsupported[:3])})"
    if not has_experience and re.search(r"experi[êe]ncia (profissional|comprovada|s[óo]lida)|atuou (em|na|como)", text, re.I):
        return "sugere experiência profissional não cadastrada"
    return None


def generate_resume_text(job: ParsedJob, profile: Profile, supported_terms: set[str], allowed: list[str]) -> dict:
    user = (
        f"CARGO DA VAGA: {job.title}\nPALAVRAS-CHAVE DA VAGA: {', '.join(job.keywords[:25])}\n"
        f"PERFIL (única fonte de fatos): {profile_facts(profile, allowed)}"
    )
    data = complete_json(RESUME_SYSTEM, user)
    title = str(data.get("title") or "").strip()[:80]
    summary = str(data.get("summary") or "").strip()[:900]
    if not summary:
        raise LLMError("A IA não retornou um resumo.")
    reason = validate_generated_text(f"{title}. {summary}", supported_terms, bool(profile.experiences))
    if reason:
        raise LLMError(f"Texto da IA rejeitado na validação: {reason}.")
    return {"title": title, "summary": summary}
