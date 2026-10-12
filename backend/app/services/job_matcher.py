"""Score de compatibilidade explicável e análise MATCH / GAPS / RISKS."""
from __future__ import annotations

import re
from collections import defaultdict

from app.models.schemas import Analysis, MatchItem, ParsedJob, Profile, ScoreComponent
from app.services.catalog import CATALOG, RELATED, canonical, display_name, find_terms

PARTIAL_CREDIT = 0.4


def build_evidence_index(profile: Profile) -> dict[str, list[str]]:
    """Termo canônico -> lista de origens no perfil (ordem de confiança: experiência, projeto, cert., competência)."""
    idx: dict[str, list[str]] = defaultdict(list)

    def add(text: str, source: str) -> None:
        for term in find_terms(text):
            if source not in idx[term]:
                idx[term].append(source)

    for e in profile.experiences:
        add(" ".join([e.role, *e.bullets]), f"experiência em {e.company}")
    for p in profile.projects:
        add(" ".join([p.name, p.description, *p.technologies, *p.bullets]), f"projeto {p.name}")
    for c in profile.certifications:
        add(c.name, f"certificação {c.name}")
    for ed in profile.education:
        add(f"{ed.course} {ed.notes}", f"formação {ed.institution}".strip())
    for a in profile.achievements:
        add(a, "conquistas")
    for cat in profile.skills:
        for item in cat.items:
            add(item, f"competências ({cat.name})")
    return idx


def profile_text(profile: Profile) -> str:
    """Texto corrido do perfil, usado para termos que não estão no catálogo (vindos da IA)."""
    return profile.model_dump_json().lower()


def evidence_text(sources: list[str]) -> str:
    return "; ".join(sources[:2])


def _related_in_profile(term: str, idx: dict[str, list[str]]) -> list[str]:
    return [display_name(r) for r in RELATED.get(term, []) if r in idx]


def profile_has_experience(profile: Profile) -> bool:
    return bool(profile.experiences)


def analyze(job: ParsedJob, profile: Profile) -> Analysis:
    idx = build_evidence_index(profile)
    ptext = profile_text(profile)
    match: list[MatchItem] = []
    gaps: list[MatchItem] = []
    risks: list[str] = []
    notices: list[str] = []

    partial_gain = {"required": 0.0, "desired": 0.0}
    counts = {"required": [0, 0], "desired": [0, 0]}  # [atendidos, total]

    for level, names in (("required", job.technologies_required), ("desired", job.technologies_desired)):
        for name in names:
            term = canonical(name)
            counts[level][1] += 1
            if term not in CATALOG and term not in idx and name.lower() in ptext:
                idx[term] = ["texto do perfil"]
            if term in idx:
                counts[level][0] += 1
                match.append(MatchItem(requirement=name, evidence=evidence_text(idx[term]), level=level))
                continue
            related = _related_in_profile(term, idx)
            if related:
                partial_gain[level] += PARTIAL_CREDIT
                gaps.append(MatchItem(
                    requirement=name,
                    evidence=f"Não comprovado diretamente. Conhecimento relacionado no perfil: {', '.join(related)}.",
                    level=level,
                ))
            else:
                gaps.append(MatchItem(requirement=name, evidence="Não encontrado no perfil.", level=level))
                if level == "required" and len([r for r in risks if r.startswith("Requisito")]) < 5:
                    risks.append(f"Requisito obrigatório sem respaldo no perfil: {name}.")

    components: list[ScoreComponent] = []

    # 1/2 — tecnologias
    for key, label, mx in (("required", "Tecnologias obrigatórias", 40.0), ("desired", "Tecnologias desejáveis", 10.0)):
        ok, total = counts[key]
        if total:
            pts = mx * min(1.0, (ok + partial_gain[key]) / total)
            expl = f"{ok} de {total} termos respaldados no perfil"
            if partial_gain[key]:
                expl += f" (crédito parcial por conhecimentos relacionados)"
            components.append(ScoreComponent(criterion=label, points=round(pts, 1), max_points=mx, explanation=expl + "."))
    if not counts["required"][1] and not counts["desired"][1]:
        notices.append("Poucos termos técnicos conhecidos foram reconhecidos na vaga; revise a análise manualmente.")

    # 3 — formação e certificações
    edu_pts, edu_expl = 0.0, []
    done = any(re.search(r"conclu", f"{e.status} {e.period}", re.I) for e in profile.education)
    ongoing = any(re.search(r"andamento|cursando", f"{e.status} {e.period}", re.I) for e in profile.education)
    if profile.education:
        if job.degree_required:
            edu_pts = 8.0 if done else (4.0 if ongoing else 0.0)
            edu_expl.append("formação superior exigida e " + ("concluída no perfil" if done else "em andamento" if ongoing else "não cadastrada"))
        else:
            edu_pts = 8.0
            edu_expl.append("formação superior cadastrada (vaga não exige explicitamente)")
    cert_hits = [c.name for c in profile.certifications if set(find_terms(c.name)) & set(canonical(k) for k in job.keywords)]
    cert_pts = 7.0 * min(1.0, len(cert_hits) / 2) if cert_hits else 0.0
    edu_expl.append(f"certificações relacionadas: {', '.join(cert_hits)}" if cert_hits else "nenhuma certificação cadastrada relacionada às tecnologias da vaga")
    components.append(ScoreComponent(criterion="Formação e certificações", points=round(edu_pts + cert_pts, 1), max_points=15.0, explanation="; ".join(edu_expl).capitalize() + "."))

    # 4 — projetos
    job_terms = [canonical(n) for n in (*job.technologies_required, *job.technologies_desired)]
    proj_terms: set[str] = set()
    related_projects = []
    for p in profile.projects:
        terms = set(find_terms(" ".join([p.description, *p.technologies, *p.bullets])))
        inter = terms & set(job_terms)
        if inter:
            related_projects.append(p.name)
        proj_terms |= terms
    if job_terms:
        overlap = len(proj_terms & set(job_terms))
        pts = 15.0 * min(1.0, overlap / min(len(job_terms), 6))
        expl = f"{overlap} termos da vaga aparecem em projetos ({', '.join(related_projects)})" if overlap else "nenhum projeto cadastrado cobre os termos da vaga"
        components.append(ScoreComponent(criterion="Projetos relacionados", points=round(pts, 1), max_points=15.0, explanation=expl + "."))

    # 5 — experiência profissional
    senior_levels = {"Pleno", "Sênior", "Especialista"}
    if profile_has_experience(profile):
        components.append(ScoreComponent(criterion="Experiência profissional", points=20.0 if not job.years_required else 14.0, max_points=20.0,
                                         explanation="Experiências cadastradas no perfil" + ("; tempo exigido não pode ser verificado automaticamente." if job.years_required else ".")))
    else:
        entry_level = job.seniority in ("Estágio", "Trainee", "Júnior") or (not job.years_required and job.seniority not in senior_levels)
        components.append(ScoreComponent(
            criterion="Experiência profissional", points=10.0 if entry_level else 0.0, max_points=20.0,
            explanation="Nenhuma experiência profissional cadastrada. " + ("A vaga não exige experiência prévia de forma clara (pontuação parcial)." if entry_level else "A vaga indica experiência prévia."),
        ))
        if job.years_required:
            risks.append(f"A vaga pede {job.years_required}+ anos de experiência e o perfil não tem experiência profissional cadastrada.")
        if job.seniority in senior_levels:
            risks.append(f"Senioridade solicitada ({job.seniority}) sem experiência profissional cadastrada no perfil.")

    if job.english_required and not profile.languages:
        risks.append("A vaga menciona inglês, mas o nível de idiomas não está cadastrado no perfil.")
    if job.degree_required and not done:
        risks.append("A vaga exige formação superior e o perfil não registra curso concluído.")
    if job.certifications_mentioned and not cert_hits:
        risks.append("A vaga menciona certificações, mas nenhuma das cadastradas parece relacionada.")

    total_max = sum(c.max_points for c in components)
    score = round(sum(c.points for c in components) / total_max * 100) if total_max else 0
    score = max(0, min(100, score))

    return Analysis(
        job=job, score=score, score_components=components, summary=_summary(score, counts, risks),
        match=match, gaps=gaps, risks=risks, mode="rules", notices=notices,
    )


def _summary(score: int, counts: dict[str, list[int]], risks: list[str]) -> str:
    ok, total = counts["required"]
    parts = [f"Compatibilidade estimada de {score}/100."]
    if total:
        parts.append(f"{ok} de {total} tecnologias/requisitos obrigatórios identificados têm respaldo no perfil.")
    dok, dtotal = counts["desired"]
    if dtotal:
        parts.append(f"{dok} de {dtotal} desejáveis atendidos.")
    if risks:
        parts.append(f"{len(risks)} ponto(s) de risco merecem atenção.")
    parts.append("Lacunas indicam informação não encontrada no perfil, não necessariamente ausência de competência. "
                 "O score é uma estimativa e não garante aprovação em ATS.")
    return " ".join(parts)
