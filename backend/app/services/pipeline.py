"""Orquestra parsing -> matching -> currículo, aplicando IA quando configurada e com fallback honesto."""
from __future__ import annotations

import logging

from app.models.schemas import Analysis, JobInput, Profile, ResumeContent
from app.services import llm_provider
from app.services.job_matcher import analyze, build_evidence_index
from app.services.job_parser import parse_job
from app.services.resume_generator import generate_resume

log = logging.getLogger("jobagent.pipeline")

RULES_NOTICE = "Modo sem IA: análise por regras e currículo por modelos. Termos fora do catálogo podem não ser reconhecidos."


def analyze_job(data: JobInput, profile: Profile) -> Analysis:
    parsed = parse_job(data.job_description, data.company, data.role)
    notices: list[str] = []
    mode = "rules"
    if llm_provider.load_config().enabled:
        try:
            parsed = llm_provider.enhance_parse(data.job_description, parsed)
            mode = "llm"
        except llm_provider.LLMError as exc:
            log.warning("IA indisponível na extração: %s", exc)
            notices.append(f"{exc} A extração usou o modo por regras.")
    if mode == "rules":
        notices.append(RULES_NOTICE)
    result = analyze(parsed, profile)
    result.mode = mode
    result.notices = notices + result.notices
    return result


def build_resume(analysis: Analysis, profile: Profile) -> tuple[ResumeContent, list[str]]:
    """Retorna (currículo, avisos). Avisos descrevem o modo usado para o texto."""
    resume, supported = generate_resume(analysis.job, analysis, profile)
    notices: list[str] = []
    if llm_provider.load_config().enabled:
        try:
            allowed = set(build_evidence_index(profile))
            text = llm_provider.generate_resume_text(analysis.job, profile, allowed, supported)
            resume.summary = text["summary"]
            if text["title"]:
                resume.title = text["title"]
            notices.append("Título e resumo redigidos pela IA e validados contra o perfil; demais seções vêm do perfil.")
        except llm_provider.LLMError as exc:
            log.warning("IA indisponível na redação: %s", exc)
            notices.append(f"{exc} Título e resumo foram gerados por modelo (sem IA).")
    else:
        notices.append("Título e resumo gerados por modelo (sem IA).")
    return resume, notices
