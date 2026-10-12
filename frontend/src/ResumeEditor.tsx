import { CsvField, LinesField, Repeater, TextArea, TextField } from "./fields";
import type { ResumeContent, SectionName } from "./types";

const ALL: SectionName[] = ["summary", "skills", "experience", "projects", "education", "certifications", "achievements", "languages"];
const LABEL: Record<SectionName, string> = {
  summary: "Resumo", skills: "Competências", experience: "Experiência", projects: "Projetos", education: "Formação",
  certifications: "Certificações", achievements: "Conquistas", languages: "Idiomas",
};

/** "Categoria: item, item" por linha. */
const skillsToText = (r: ResumeContent) => r.skills.map((g) => `${g.category}: ${g.items.join(", ")}`).join("\n");
const textToSkills = (t: string) =>
  t.split("\n").map((line) => {
    const i = line.indexOf(":");
    return i < 0 ? { category: line, items: [] as string[] } : { category: line.slice(0, i).trim(), items: line.slice(i + 1).split(",").map((x) => x.trim()) };
  });

export default function ResumeEditor({ r, onChange }: { r: ResumeContent; onChange: (r: ResumeContent) => void }) {
  const set = (patch: Partial<ResumeContent>) => onChange({ ...r, ...patch });
  const active = r.section_order;
  const move = (i: number, d: number) => {
    const j = i + d;
    if (j < 0 || j >= active.length) return;
    const next = [...active];
    [next[i], next[j]] = [next[j], next[i]];
    set({ section_order: next });
  };
  const toggle = (s: SectionName) => set({ section_order: active.includes(s) ? active.filter((x) => x !== s) : [...active, s] });

  return (
    <div className="editor">
      <fieldset className="group">
        <legend>Seções e ordem</legend>
        <p className="hint">Marque as seções que entram no arquivo e ajuste a ordem. Seções vazias não são exportadas.</p>
        <ol className="order-list">
          {active.map((s, i) => (
            <li key={s}>
              <label><input type="checkbox" checked onChange={() => toggle(s)} /> {LABEL[s]}</label>
              <span className="row-actions">
                <button type="button" className="btn small ghost" onClick={() => move(i, -1)} disabled={i === 0} aria-label={`Subir ${LABEL[s]}`}>↑</button>
                <button type="button" className="btn small ghost" onClick={() => move(i, 1)} disabled={i === active.length - 1} aria-label={`Descer ${LABEL[s]}`}>↓</button>
              </span>
            </li>
          ))}
        </ol>
        <div className="chips">
          {ALL.filter((s) => !active.includes(s)).map((s) => <button type="button" key={s} className="btn small" onClick={() => toggle(s)}>+ {LABEL[s]}</button>)}
        </div>
      </fieldset>

      <fieldset className="group">
        <legend>Cabeçalho</legend>
        <div className="grid2">
          <TextField label="Nome" value={r.name} onChange={(name) => set({ name })} />
          <TextField label="Título profissional" value={r.title} onChange={(title) => set({ title })} />
        </div>
        <LinesField label="Contatos (e-mail, telefone, cidade)" value={r.contacts} onChange={(contacts) => set({ contacts })} rows={3} />
        <Repeater title="Links" items={r.links} onChange={(links) => set({ links })} addLabel="Adicionar link" make={() => ({ label: "", url: "" })} itemLabel={(l) => l.label}
          render={(l, u) => <div className="grid2"><TextField label="Rótulo" value={l.label} onChange={(label) => u({ label })} /><TextField label="URL" value={l.url} onChange={(url) => u({ url })} /></div>} />
      </fieldset>

      <fieldset className="group">
        <legend>Resumo profissional</legend>
        <TextArea label="Resumo" value={r.summary} rows={6} onChange={(summary) => set({ summary })} />
      </fieldset>

      <fieldset className="group">
        <legend>Competências técnicas</legend>
        <TextArea label="Uma categoria por linha" value={skillsToText(r)} rows={6} hint="Formato: Categoria: item, item, item" onChange={(t) => set({ skills: textToSkills(t) })} />
      </fieldset>

      <Repeater title="Experiência profissional" items={r.experience} onChange={(experience) => set({ experience })} addLabel="Adicionar experiência"
        make={() => ({ company: "", role: "", period: "", bullets: [] })} itemLabel={(e) => `${e.role} — ${e.company}`}
        render={(e, u) => (<>
          <div className="grid2">
            <TextField label="Cargo" value={e.role} onChange={(role) => u({ role })} />
            <TextField label="Empresa" value={e.company} onChange={(company) => u({ company })} />
            <TextField label="Período" value={e.period} onChange={(period) => u({ period })} />
          </div>
          <LinesField label="Atividades" value={e.bullets} onChange={(bullets) => u({ bullets })} />
        </>)} />

      <Repeater title="Projetos" items={r.projects} onChange={(projects) => set({ projects })} addLabel="Adicionar projeto"
        make={() => ({ name: "", subtitle: "", description: "", technologies: [], bullets: [], link: "" })} itemLabel={(p) => p.name}
        render={(p, u) => (<>
          <div className="grid2">
            <TextField label="Nome" value={p.name} onChange={(name) => u({ name })} />
            <TextField label="Subtítulo" value={p.subtitle} onChange={(subtitle) => u({ subtitle })} />
            <TextField label="Link" value={p.link} onChange={(link) => u({ link })} />
          </div>
          <TextArea label="Descrição" value={p.description} rows={2} onChange={(description) => u({ description })} />
          <LinesField label="Pontos de destaque" value={p.bullets} onChange={(bullets) => u({ bullets })} />
          <CsvField label="Tecnologias" value={p.technologies} onChange={(technologies) => u({ technologies })} />
        </>)} />

      <Repeater title="Formação acadêmica" items={r.education} onChange={(education) => set({ education })} addLabel="Adicionar formação"
        make={() => ({ course: "", institution: "", period: "", notes: "" })} itemLabel={(e) => e.course}
        render={(e, u) => (
          <div className="grid2">
            <TextField label="Curso" value={e.course} onChange={(course) => u({ course })} />
            <TextField label="Instituição" value={e.institution} onChange={(institution) => u({ institution })} />
            <TextField label="Período" value={e.period} onChange={(period) => u({ period })} />
            <TextField label="Observações" value={e.notes} onChange={(notes) => u({ notes })} />
          </div>
        )} />

      <fieldset className="group">
        <legend>Listas</legend>
        <LinesField label="Certificações" value={r.certifications} onChange={(certifications) => set({ certifications })} rows={4} />
        <LinesField label="Conquistas" value={r.achievements} onChange={(achievements) => set({ achievements })} rows={3} />
        <LinesField label="Idiomas" value={r.languages} onChange={(languages) => set({ languages })} rows={2} />
      </fieldset>
    </div>
  );
}
