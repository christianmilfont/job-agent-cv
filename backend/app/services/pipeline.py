"""Orquestra parsing -> matching -> currículo, aplicando IA quando configurada e com fallback honesto."""
from __future__ import annotations

import logging

from app.models.schemas import Analysis, JobInput, Profile, ResumeContent
from app.services import llm_provider
from app.services.job_matcher import analyze, build_evidence_index
from app.services.job_parser import parse_job
from app.services.resume_generator import generate_resume
from app.telemetry import tracer

log = logging.getLogger("jobagent.pipeline")

RULES_NOTICE = "Modo sem IA: análise por regras e currículo por modelos. Termos fora do catálogo podem não ser reconhecidos."


def analyze_job(data: JobInput, profile: Profile) -> Analysis:
    with tracer.start_as_current_span("pipeline.analyze_job") as span:
        span.set_attribute("job.chars", len(data.job_description))
        with tracer.start_as_current_span("job.parse_rules"):
            parsed = parse_job(data.job_description, data.company, data.role)
        notices: list[str] = []
        mode = "rules"
        cfg = llm_provider.load_config()
        if cfg.enabled:
            try:
                with tracer.start_as_current_span("llm.enhance_parse"):
                    parsed = llm_provider.enhance_parse(data.job_description, parsed)
                mode = "llm"
            except llm_provider.LLMError as exc:
                log.warning("IA indisponível na extração: %s", exc)
                span.add_event("llm.fallback", {"stage": "parse"})
                notices.append(f"{exc} A extração usou o modo por regras.")
        if mode == "rules":
            notices.append(RULES_NOTICE)
        with tracer.start_as_current_span("job.match") as m:
            result = analyze(parsed, profile)
            m.set_attribute("match.score", result.score)
            m.set_attribute("match.gaps", len(result.gaps))
        result.mode = mode
        result.notices = notices + result.notices
        span.set_attribute("pipeline.mode", mode)
        return result


def build_resume(analysis: Analysis, profile: Profile) -> tuple[ResumeContent, list[str]]:
    """Retorna (currículo, avisos). Avisos descrevem o modo usado para o texto."""
    with tracer.start_as_current_span("pipeline.build_resume") as span:
        with tracer.start_as_current_span("resume.generate_rules"):
            resume, supported = generate_resume(analysis.job, analysis, profile)
        notices: list[str] = []
        mode = "rules"
        if llm_provider.load_config().enabled:
            try:
                with tracer.start_as_current_span("llm.generate_resume_text"):
                    allowed = set(build_evidence_index(profile))
                    text = llm_provider.generate_resume_text(analysis.job, profile, allowed, supported)
                resume.summary = text["summary"]
                if text["title"]:
                    resume.title = text["title"]
                mode = "llm"
                notices.append("Título e resumo redigidos pela IA e validados contra o perfil; demais seções vêm do perfil.")
            except llm_provider.LLMError as exc:
                log.warning("IA indisponível na redação: %s", exc)
                span.add_event("llm.fallback", {"stage": "resume_text"})
                notices.append(f"{exc} Título e resumo foram gerados por modelo (sem IA).")
        else:
            notices.append("Título e resumo gerados por modelo (sem IA).")
        span.set_attribute("pipeline.mode", mode)
        return resume, notices
