"""Schemas Pydantic compartilhados por API, serviços e persistência."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

MAX_JOB_CHARS = 30_000
MIN_JOB_CHARS = 40


# ---------------------------------------------------------------- Perfil
class Personal(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class Education(BaseModel):
    course: str
    institution: str = ""
    period: str = ""
    status: str = ""
    notes: str = ""


class Certification(BaseModel):
    name: str
    issuer: str = ""


class SkillCategory(BaseModel):
    name: str
    items: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    subtitle: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    link: str = ""


class Experience(BaseModel):
    company: str
    role: str
    start: str = ""
    end: str = ""
    location: str = ""
    bullets: list[str] = Field(default_factory=list)


class Language(BaseModel):
    name: str
    level: str = ""


class Profile(BaseModel):
    personal: Personal = Field(default_factory=Personal)
    education: list[Education] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    skills: list[SkillCategory] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)


# ---------------------------------------------------------------- Vaga
class JobInput(BaseModel):
    job_description: str
    company: str = ""
    role: str = ""

    @field_validator("job_description")
    @classmethod
    def _check_description(cls, v: str) -> str:
        v = v.strip()
        if len(v) < MIN_JOB_CHARS:
            raise ValueError("A descrição da vaga está muito curta. Cole o texto completo da vaga.")
        if len(v) > MAX_JOB_CHARS:
            raise ValueError(f"A descrição da vaga excede {MAX_JOB_CHARS} caracteres.")
        return v

    @field_validator("company", "role")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()[:200]


class JobRequirement(BaseModel):
    name: str
    kind: Literal["tech", "other"] = "tech"
    level: Literal["required", "desired"] = "required"


class ParsedJob(BaseModel):
    title: str = ""
    company: str = ""
    seniority: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    required: list[str] = Field(default_factory=list)
    desired: list[str] = Field(default_factory=list)
    technologies_required: list[str] = Field(default_factory=list)
    technologies_desired: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    years_required: Optional[int] = None
    degree_required: bool = False
    english_required: bool = False
    certifications_mentioned: bool = False


# ---------------------------------------------------------------- Compatibilidade
class MatchItem(BaseModel):
    requirement: str
    evidence: str = ""  # onde no perfil há respaldo
    level: Literal["required", "desired"] = "required"


class ScoreComponent(BaseModel):
    criterion: str
    points: float
    max_points: float
    explanation: str


class Analysis(BaseModel):
    job: ParsedJob
    score: int
    score_components: list[ScoreComponent] = Field(default_factory=list)
    summary: str = ""
    match: list[MatchItem] = Field(default_factory=list)
    gaps: list[MatchItem] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    mode: Literal["rules", "llm"] = "rules"
    notices: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- Currículo
class ResumeLink(BaseModel):
    label: str
    url: str


class ResumeSkillGroup(BaseModel):
    category: str
    items: list[str] = Field(default_factory=list)


class ResumeProject(BaseModel):
    name: str
    subtitle: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    link: str = ""


class ResumeEducation(BaseModel):
    course: str
    institution: str = ""
    period: str = ""
    notes: str = ""


class ResumeExperience(BaseModel):
    company: str
    role: str
    period: str = ""
    bullets: list[str] = Field(default_factory=list)


SectionName = Literal[
    "summary", "skills", "experience", "projects", "education", "certifications", "achievements", "languages"
]


class ResumeContent(BaseModel):
    name: str = ""
    title: str = ""
    contacts: list[str] = Field(default_factory=list)  # e-mail, telefone, local
    links: list[ResumeLink] = Field(default_factory=list)
    summary: str = ""
    skills: list[ResumeSkillGroup] = Field(default_factory=list)
    experience: list[ResumeExperience] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    education: list[ResumeEducation] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    section_order: list[SectionName] = Field(
        default_factory=lambda: ["summary", "skills", "projects", "education", "certifications"]
    )


# ---------------------------------------------------------------- Candidaturas
class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    resume: Optional[ResumeContent] = None


class Application(BaseModel):
    id: int
    company: str
    role: str
    job_description: str
    created_at: str
    updated_at: str
    score: int
    analysis: Analysis
    resume_generated: ResumeContent
    resume: ResumeContent  # versão editável


class ApplicationSummary(BaseModel):
    id: int
    company: str
    role: str
    created_at: str
    score: int
    mode: str


class AppStatus(BaseModel):
    ai_enabled: bool
    provider: str
    model: str
    mode: Literal["rules", "llm"]
    message: str
