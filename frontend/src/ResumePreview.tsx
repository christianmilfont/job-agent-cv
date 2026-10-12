import type { ResumeContent } from "./types";

const TITLES: Record<string, string> = {
  summary: "Resumo profissional", skills: "Competências técnicas", experience: "Experiência profissional", projects: "Projetos",
  education: "Formação acadêmica", certifications: "Certificações", achievements: "Conquistas", languages: "Idiomas",
};

const short = (u: string) => u.replace(/^https?:\/\//, "").replace(/\/$/, "");

/** Pré-visualização HTML fiel à estrutura do arquivo (coluna única, sem tabelas). O PDF final é renderizado pelo servidor. */
export default function ResumePreview({ r }: { r: ResumeContent }) {
  const seen = new Set<string>();
  const order = r.section_order.filter((s) => !seen.has(s) && !!seen.add(s));
  const has: Record<string, boolean> = {
    summary: !!r.summary.trim(), skills: r.skills.length > 0, experience: r.experience.length > 0, projects: r.projects.length > 0,
    education: r.education.length > 0, certifications: r.certifications.length > 0, achievements: r.achievements.length > 0, languages: r.languages.length > 0,
  };
  const ul = (xs: string[]) => <ul>{xs.filter((x) => x.trim()).map((x, i) => <li key={i}>{x}</li>)}</ul>;
  return (
    <article className="paper" aria-label="Pré-visualização do currículo">
      {r.name && <h1>{r.name}</h1>}
      {r.title && <p className="p-title">{r.title}</p>}
      <p className="p-contact">
        {[...r.contacts.map((c) => <span key={c}>{c}</span>), ...r.links.map((l) => <a key={l.url} href={l.url} target="_blank" rel="noreferrer">{l.label}: {short(l.url)}</a>)]
          .flatMap((el, i) => (i ? [" | ", el] : [el]))}
      </p>
      {order.filter((s) => has[s]).map((s) => (
        <section key={s}>
          <h2>{TITLES[s]}</h2>
          {s === "summary" && <p>{r.summary}</p>}
          {s === "skills" && r.skills.map((g, i) => <p key={i}><strong>{g.category}:</strong> {g.items.join(", ")}</p>)}
          {s === "experience" && r.experience.map((e, i) => (
            <div key={i}><h3>{e.role} — {e.company}{e.period && ` (${e.period})`}</h3>{ul(e.bullets)}</div>
          ))}
          {s === "projects" && r.projects.map((p, i) => (
            <div key={i}>
              <h3>{p.name}{p.subtitle && ` — ${p.subtitle}`}</h3>
              {p.description && <p>{p.description}</p>}
              {ul(p.bullets)}
              {p.technologies.length > 0 && <p className="meta"><em>Tecnologias:</em> {p.technologies.join(", ")}</p>}
              {p.link && <p className="meta"><a href={p.link} target="_blank" rel="noreferrer">{p.link}</a></p>}
            </div>
          ))}
          {s === "education" && r.education.map((e, i) => (
            <div key={i}><h3>{e.course}{e.institution && ` — ${e.institution}`}</h3><p className="meta">{[e.period, e.notes].filter(Boolean).join(" | ")}</p></div>
          ))}
          {(s === "certifications" || s === "achievements" || s === "languages") && ul(r[s])}
        </section>
      ))}
    </article>
  );
}
