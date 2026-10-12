"""Geração do currículo por regras/templates, usando apenas fatos do perfil."""
from __future__ import annotations

import re

from app.models.schemas import (
    Analysis, ParsedJob, Profile, ResumeContent, ResumeEducation, ResumeExperience, ResumeLink,
    ResumeProject, ResumeSkillGroup,
)
from app.services.catalog import area_of, canonical, find_terms
from app.services.job_matcher import build_evidence_index

CLOUDISH = {"cloud", "devops", "observability", "security"}
DOMAIN_LABEL = {
    "cloud": "DevOps e Arquitetura Cloud", "devops": "DevOps e Arquitetura Cloud",
    "observability": "DevOps e Observabilidade", "security": "DevSecOps",
    "backend": "Desenvolvimento de Software", "frontend": "Desenvolvimento de Software",
    "data": "Dados e Engenharia de Dados", "ai": "Inteligência Artificial", "mobile": "Desenvolvimento Mobile",
}
STRIP_TITLE = re.compile(r"\b(pleno|pl|s[êe]nior|sr\.?|senior|especialista|staff|principal|lead|l[íi]der)\b\.?", re.I)


def job_priority(job: ParsedJob) -> dict[str, int]:
    """Termo canônico -> prioridade (0 = mais importante). Obrigatórias, depois desejáveis, depois palavras-chave."""
    order: dict[str, int] = {}
    for name in [*job.technologies_required, *job.technologies_desired, *job.keywords]:
        order.setdefault(canonical(name), len(order))
    return order


def _short_title(job_title: str) -> str:
    t = re.split(r"\s[|•–—]\s|\s-\s|\(", job_title)[0]
    t = STRIP_TITLE.sub("", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" -–|,/")
    return t[:60]


def build_title(job: ParsedJob, supported: list[str]) -> str:
    if job.title:
        t = _short_title(job.title)
        if len(t) >= 3:
            return t
    areas = [area_of(t) for t in supported if area_of(t) in DOMAIN_LABEL]
    if areas:
        dominant = max(set(areas), key=areas.count)
        return f"Profissional de TI | {DOMAIN_LABEL[dominant]}"
    return "Profissional de Tecnologia da Informação"


def _first_sentence(text: str) -> str:
    return re.split(r"[:.]", text, 1)[0].strip()


def build_summary(profile: Profile, job: ParsedJob, supported: list[str], projects: list[ResumeProject], cert_names: list[str]) -> str:
    parts: list[str] = []
    done = [e for e in profile.education if re.search(r"conclu", f"{e.status} {e.period}", re.I)]
    ongoing = [e for e in profile.education if e not in done and re.search(r"andamento|cursando", f"{e.status} {e.period}", re.I)]
    edu_bits = []
    for e in done[:1]:
        edu_bits.append(f"{e.course}{' pela ' + e.institution if e.institution else ''}{' (' + e.period.lower() + ')' if e.period else ''}")
    for e in ongoing[:1]:
        edu_bits.append(f"{e.course}{' na ' + e.institution if e.institution else ''} (em andamento)")
    if edu_bits:
        parts.append("Formação: " + "; ".join(edu_bits) + ".")
    top = supported[:6]
    proj_names = [p.name for p in projects if p.name and "acadêmic" not in p.name.lower()][:2]
    if top:
        where = f"estudos e projetos acadêmicos e de portfólio (como {' e '.join(proj_names)})" if proj_names else "estudos e projetos acadêmicos e de portfólio"
        txt = f"Conhecimentos explorados em {where}: {', '.join(top)}"
        parts.append(txt + ".")
    return " ".join(parts)


def top_bullets(bullets: list[str], prio: dict[str, int], n: int) -> list[str]:
    """Até n pontos, escolhendo os que mais citam termos da vaga e mantendo a ordem original."""
    ranked = sorted(range(len(bullets)), key=lambda i: (-sum(1 for t in find_terms(bullets[i]) if t in prio), i))
    return [bullets[i] for i in sorted(ranked[:n])]


def select_skills(profile: Profile, prio: dict[str, int]) -> list[ResumeSkillGroup]:
    scored = []
    for pos, cat in enumerate(profile.skills):
        matched, rest = [], []
        for item in cat.items:
            ranks = [prio[t] for t in find_terms(item) if t in prio]
            (matched if ranks else rest).append((min(ranks) if ranks else 0, item))
        matched.sort(key=lambda x: x[0])
        scored.append((len(matched), pos, cat.name, [i for _, i in matched], [i for _, i in rest]))
    groups = [
        ResumeSkillGroup(category=name, items=m + r[:2])
        for n, _pos, name, m, r in sorted((s for s in scored if s[0]), key=lambda s: (-s[0], s[1]))
    ]
    if len(groups) < 2:  # vaga com poucos termos reconhecidos: mantém um núcleo do perfil
        have = {g.category for g in groups}
        for _n, _pos, name, m, r in sorted(scored, key=lambda s: s[1]):
            if name not in have and len(groups) < 2 and (m or r):
                groups.append(ResumeSkillGroup(category=name, items=(m + r)[:5]))
    return groups


def select_projects(profile: Profile, prio: dict[str, int], job: ParsedJob) -> list[ResumeProject]:
    req = {canonical(t) for t in job.technologies_required}
    ranked = []
    for pos, p in enumerate(profile.projects):
        terms = set(find_terms(" ".join([p.description, *p.technologies, *p.bullets])))
        score = sum(2 if t in req else 1 for t in terms if t in prio)
        ranked.append((score, -pos, p, terms))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    chosen = [r for r in ranked if r[0] > 0][:2] or ranked[:1]
    out = []
    for _score, _p, p, _terms in chosen:
        def brank(b: str) -> int:
            return -sum(1 for t in find_terms(b) if t in prio)
        bullets = top_bullets(p.bullets, prio, 2)
        techs = sorted(p.technologies, key=lambda t: min([prio[x] for x in find_terms(t) if x in prio] or [999]))[:6]
        out.append(ResumeProject(name=p.name, subtitle=p.subtitle, description="" if bullets else p.description, technologies=techs, bullets=bullets, link=p.link))
    return out


def select_certifications(profile: Profile, prio: dict[str, int]) -> list[str]:
    ranked = []
    for pos, c in enumerate(profile.certifications):
        rel = sum(1 for t in find_terms(c.name) if t in prio)
        ranked.append((rel, -pos, c))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    chosen = [r for r in ranked if r[0] > 0]
    if len(chosen) < 2:
        chosen = ranked[:2]
    return [f"{c.name}{' — ' + c.issuer if c.issuer and c.issuer.lower() not in c.name.lower() else ''}" for _r, _p, c in chosen]


def generate_resume(job: ParsedJob, analysis: Analysis, profile: Profile) -> tuple[ResumeContent, list[str]]:
    """Retorna (currículo, termos da vaga com respaldo no perfil)."""
    idx = build_evidence_index(profile)
    prio = job_priority(job)
    supported = [t for t in prio if t in idx]
    from app.services.catalog import display_name
    supported_display = [display_name(t) for t in supported]

    projects = select_projects(profile, prio, job)
    certs = select_certifications(profile, prio)
    cert_hit_count = sum(1 for c in profile.certifications if any(t in prio for t in find_terms(c.name)))

    p = profile.personal
    contacts = [x for x in (p.email, p.phone, p.location) if x]
    links = [ResumeLink(label=l, url=u) for l, u in (("LinkedIn", p.linkedin), ("GitHub", p.github), ("Portfólio", p.portfolio)) if u]

    experience = [
        ResumeExperience(company=e.company, role=e.role, period=" – ".join(x for x in (e.start, e.end) if x) + (f" | {e.location}" if e.location else ""), bullets=top_bullets(e.bullets, prio, 3))
        for e in profile.experiences
    ]
    education = [ResumeEducation(course=e.course, institution=e.institution, period=e.period, notes=e.notes) for e in profile.education]
    achievements = profile.achievements[:1] if profile.achievements and any(area_of(t) in CLOUDISH for t in supported) else []
    languages = [f"{l.name}{' — ' + l.level if l.level else ''}" for l in profile.languages]

    order = ["summary", "skills"]
    if experience:
        order.append("experience")
    if cert_hit_count >= 2 or job.certifications_mentioned:
        order += ["certifications", "projects", "education"]
    else:
        order += ["projects", "education", "certifications"]
    if achievements:
        order.append("achievements")
    if languages:
        order.append("languages")

    resume = ResumeContent(
        name=p.full_name, title=build_title(job, supported_display), contacts=contacts, links=links,
        summary=build_summary(profile, job, supported_display, projects, [c.split(" — ")[0] for c in certs[:cert_hit_count] or certs]),
        skills=select_skills(profile, prio), experience=experience, projects=projects, education=education,
        certifications=certs, achievements=achievements, languages=languages, section_order=order,
    )
    return resume, supported
