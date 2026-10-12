"""Extração de requisitos baseada em regras (modo sem IA). Não inventa nada: só o que está no texto."""
from __future__ import annotations

import re

from app.models.schemas import ParsedJob
from app.services.catalog import SOFT_SKILLS, display_name, find_terms

SECTION_PATTERNS = {
    "responsibilities": r"responsabilidades|atividades|atribuições|atribuicoes|o que (você|voce) vai fazer|what you.ll do|responsibilities|dia a dia|principais entregas",
    "required": r"requisitos|qualificações|qualificacoes|requirements|o que buscamos|o que esperamos|what we.re looking for|pré-requisitos|pre-requisitos|conhecimentos necessários|obrigat",
    "desired": r"desejáve|desejave|diferencia|nice to have|plus|será um plus|seria bom|bonus|bônus",
    "other": r"benefícios|beneficios|benefits|sobre (a|nós|nos)|about|remuneração|salário|processo seletivo|nossa cultura|how to apply|como se candidatar",
}
DESIRED_LINE = re.compile(r"desejáve|desejave|diferencial|nice to have|será um plus|um plus|\bplus\b|bônus|bonus", re.I)

SENIORITY = [
    ("Estágio", r"\best[áa]gi[oá]?r?i?[oa]?\b|\bintern(ship)?\b"),
    ("Trainee", r"\btrainee\b"),
    ("Júnior", r"\bj[úu]nior\b|\bjr\.?\b|\bjunior\b"),
    ("Pleno", r"\bpleno\b|\bmid[- ]level\b|\bpl\b"),
    ("Sênior", r"\bs[êe]nior\b|\bsr\.?\b|\bsenior\b"),
    ("Especialista", r"\bespecialista\b|\bstaff\b|\bprincipal\b|\blead\b|\bl[ií]der\b"),
]

BULLET = re.compile(r"^\s*(?:[-•*·▪●◦–]|\d+[.)])\s+")


def _clean_line(line: str) -> str:
    return BULLET.sub("", line).strip(" \t-•*")


def _section_for(line: str) -> str | None:
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > 70 or BULLET.match(line):
        return None
    if not (line.strip().endswith(":") or stripped.isupper() or len(stripped.split()) <= 6):
        return None
    for name in ("desired", "required", "responsibilities", "other"):
        if re.search(SECTION_PATTERNS[name], stripped, re.I):
            return name
    return None


def _guess_title_company(text: str) -> tuple[str, str]:
    title = company = ""
    m = re.search(r"^\s*(?:vaga|cargo|t[íi]tulo|posi[çc][ãa]o|job title)\s*[:\-–]\s*(.+)$", text, re.I | re.M)
    if m:
        title = m.group(1).strip()
    m = re.search(r"^\s*(?:empresa|company|organiza[çc][ãa]o)\s*[:\-–]\s*(.+)$", text, re.I | re.M)
    if m:
        company = m.group(1).strip()
    if not title:
        for line in text.splitlines():
            line = line.strip()
            if line:
                if len(line) <= 80 and not line.endswith((".", ":")) and not BULLET.match(line):
                    title = line
                break
    # "Cargo - Empresa": separa quando o trecho final não parece modalidade/local.
    if title and not company:
        parts = re.split(r"\s+[-–—|]\s+", title)
        tail = parts[-1] if len(parts) > 1 else ""
        if tail and len(tail.split()) <= 4 and not re.search(r"remot|h[íi]brid|presencial|home|\b(?:clt|pj|sp|rj)\b|s[ãa]o paulo|brasil", tail, re.I):
            title, company = " - ".join(parts[:-1]), tail
    return title[:120], company[:120]


def _detect_seniority(text: str, title: str) -> str:
    head = title + "\n" + text[:600]
    for label, pat in SENIORITY:
        if re.search(pat, head, re.I):
            return label
    for label, pat in SENIORITY:
        if re.search(pat, text, re.I) and label != "Pleno":
            return label
    return ""


def _soft_skills(text: str) -> list[str]:
    low = text.lower()
    return [n for n, keys in SOFT_SKILLS.items() if any(k in low for k in keys)]


def _years(text: str) -> int | None:
    vals = [int(m.group(1)) for m in re.finditer(r"(\d{1,2})\s*\+?\s*(?:anos?|years?)\s+(?:de\s+)?(?:experi[êe]ncia|experience|atuando|na [áa]rea)", text, re.I)]
    vals += [int(m.group(1)) for m in re.finditer(r"experi[êe]ncia[^.\n]{0,40}?(?:m[íi]nima de |de |m[ií]nimo de )?(\d{1,2})\s*\+?\s*anos", text, re.I)]
    return max(vals) if vals else None


def parse_job(text: str, company: str = "", role: str = "") -> ParsedJob:
    lines = [ln for ln in text.splitlines()]
    section = "responsibilities"
    seen_section = False
    buckets: dict[str, list[str]] = {"responsibilities": [], "required": [], "desired": [], "other": []}
    tech_level: dict[str, str] = {}  # canônico -> required|desired

    for raw in lines:
        if not raw.strip():
            continue
        new = _section_for(raw)
        if new:
            section, seen_section = new, True
            continue
        item = _clean_line(raw)
        if len(item) < 3:
            continue
        # Linha dentro de seção "required" mas marcada como desejável.
        eff = section
        if eff in ("required", "responsibilities") and DESIRED_LINE.search(item):
            eff = "desired"
        if not seen_section:
            eff = "responsibilities" if BULLET.match(raw) else "other"
        buckets[eff].append(item[:300])
        if eff == "other":
            continue
        for term in find_terms(item):
            level = "desired" if eff == "desired" else "required"
            if eff == "responsibilities" and seen_section:
                level = "required"
            # 'required' prevalece sobre 'desired' se citado nos dois lugares
            if tech_level.get(term) != "required":
                tech_level[term] = level

    # Sem seções: tecnologias do texto inteiro (exceto linhas "other") entram como obrigatórias.
    if not tech_level:
        for term in find_terms(text):
            tech_level[term] = "required"

    # Termos mencionados em linhas "other" (ex.: título, texto corrido) ainda contam como palavras-chave.
    all_terms = find_terms(text)
    for term in all_terms:
        tech_level.setdefault(term, "desired")

    guessed_title, guessed_company = _guess_title_company(text)
    title = role or guessed_title
    comp = company or guessed_company
    tech_req = [display_name(t) for t in all_terms if tech_level.get(t) == "required"]
    tech_des = [display_name(t) for t in all_terms if tech_level.get(t) == "desired"]

    low = text.lower()
    return ParsedJob(
        title=title,
        company=comp,
        seniority=_detect_seniority(text, title),
        responsibilities=buckets["responsibilities"][:12],
        required=buckets["required"][:20],
        desired=buckets["desired"][:15],
        technologies_required=tech_req,
        technologies_desired=tech_des,
        soft_skills=_soft_skills(text),
        keywords=[display_name(t) for t in all_terms],
        years_required=_years(text),
        degree_required=bool(re.search(r"gradua[çc][ãa]o|ensino superior|bacharel|tecn[óo]log|cursando|superior completo|forma[çc][ãa]o em", low)),
        english_required=bool(re.search(r"ingl[êe]s|english", low)),
        certifications_mentioned=bool(re.search(r"certifica[çc]", low)),
    )
