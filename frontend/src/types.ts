export interface Personal { full_name: string; email: string; phone: string; location: string; linkedin: string; github: string; portfolio: string }
export interface Education { course: string; institution: string; period: string; status: string; notes: string }
export interface Certification { name: string; issuer: string }
export interface SkillCategory { name: string; items: string[] }
export interface Project { name: string; subtitle: string; description: string; technologies: string[]; bullets: string[]; link: string }
export interface Experience { company: string; role: string; start: string; end: string; location: string; bullets: string[] }
export interface Language { name: string; level: string }
export interface Profile {
  personal: Personal; education: Education[]; achievements: string[]; certifications: Certification[];
  skills: SkillCategory[]; projects: Project[]; experiences: Experience[]; languages: Language[];
}

export interface ParsedJob {
  title: string; company: string; seniority: string; responsibilities: string[]; required: string[]; desired: string[];
  technologies_required: string[]; technologies_desired: string[]; soft_skills: string[]; keywords: string[];
  years_required: number | null; degree_required: boolean; english_required: boolean; certifications_mentioned: boolean;
}
export interface MatchItem { requirement: string; evidence: string; level: "required" | "desired" }
export interface ScoreComponent { criterion: string; points: number; max_points: number; explanation: string }
export interface Analysis {
  job: ParsedJob; score: number; score_components: ScoreComponent[]; summary: string;
  match: MatchItem[]; gaps: MatchItem[]; risks: string[]; mode: "rules" | "llm"; notices: string[];
}

export type SectionName = "summary" | "skills" | "experience" | "projects" | "education" | "certifications" | "achievements" | "languages";
export interface ResumeContent {
  name: string; title: string; contacts: string[]; links: { label: string; url: string }[]; summary: string;
  skills: { category: string; items: string[] }[];
  experience: { company: string; role: string; period: string; bullets: string[] }[];
  projects: Project[];
  education: { course: string; institution: string; period: string; notes: string }[];
  certifications: string[]; achievements: string[]; languages: string[]; section_order: SectionName[];
}

export interface Application {
  id: number; company: string; role: string; job_description: string; created_at: string; updated_at: string;
  score: number; analysis: Analysis; resume_generated: ResumeContent; resume: ResumeContent;
}
export interface ApplicationSummary { id: number; company: string; role: string; created_at: string; score: number; mode: string }
export interface AppStatus { ai_enabled: boolean; provider: string; model: string; mode: "rules" | "llm"; message: string }
