import { useEffect, useState } from "react";
import { api } from "./api";
import { CsvField, LinesField, Repeater, TextArea, TextField, clean } from "./fields";
import type { Profile } from "./types";

const cleanProfile = (p: Profile): Profile => ({
  ...p,
  achievements: clean(p.achievements),
  skills: p.skills.map((s) => ({ ...s, items: clean(s.items) })).filter((s) => s.name.trim()),
  projects: p.projects.map((x) => ({ ...x, technologies: clean(x.technologies), bullets: clean(x.bullets) })).filter((x) => x.name.trim()),
  experiences: p.experiences.map((x) => ({ ...x, bullets: clean(x.bullets) })).filter((x) => x.company.trim() && x.role.trim()),
  education: p.education.filter((e) => e.course.trim()),
  certifications: p.certifications.filter((c) => c.name.trim()),
  languages: p.languages.filter((l) => l.name.trim()),
});

export default function ProfileEditor({ onBack }: { onBack: () => void }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.getProfile().then(setProfile).catch((e) => setError(e.message)); }, []);

  if (!profile) return <main className="container">{error ? <p className="alert error" role="alert">{error}</p> : <p aria-busy="true">Carregando perfil…</p>}</main>;

  const set = (patch: Partial<Profile>) => { setProfile({ ...profile, ...patch }); setMsg(""); };
  const pe = profile.personal;
  const setPersonal = (patch: Partial<Profile["personal"]>) => set({ personal: { ...pe, ...patch } });

  async function save() {
    setSaving(true); setError(""); setMsg("");
    try { setProfile(await api.saveProfile(cleanProfile(profile!))); setMsg("Perfil salvo."); }
    catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  }

  async function reset() {
    if (!window.confirm("Restaurar o perfil inicial? Suas edições no perfil serão descartadas (candidaturas salvas não mudam).")) return;
    try { setProfile(await api.resetProfile()); setMsg("Perfil inicial restaurado."); } catch (e) { setError((e as Error).message); }
  }

  return (
    <main className="container">
      <div className="page-head">
        <button className="btn ghost" onClick={onBack}>← Voltar</button>
        <h1>Perfil profissional</h1>
      </div>
      <p className="lead">
        Esta é a base usada em todas as candidaturas. Só entra no currículo o que estiver aqui — campos vazios ficam de fora.
        Contato, idiomas e experiências profissionais ainda precisam ser preenchidos por você.
      </p>

      <fieldset className="group">
        <legend>Dados pessoais e contato</legend>
        <div className="grid2">
          <TextField label="Nome completo" value={pe.full_name} onChange={(v) => setPersonal({ full_name: v })} hint="Confirme a grafia do seu nome." />
          <TextField label="E-mail" type="email" value={pe.email} onChange={(v) => setPersonal({ email: v })} />
          <TextField label="Telefone" value={pe.phone} onChange={(v) => setPersonal({ phone: v })} />
          <TextField label="Cidade / UF" value={pe.location} onChange={(v) => setPersonal({ location: v })} />
          <TextField label="LinkedIn" value={pe.linkedin} onChange={(v) => setPersonal({ linkedin: v })} />
          <TextField label="GitHub" value={pe.github} onChange={(v) => setPersonal({ github: v })} />
          <TextField label="Portfólio" value={pe.portfolio} onChange={(v) => setPersonal({ portfolio: v })} />
        </div>
      </fieldset>

      <Repeater title="Formação acadêmica" items={profile.education} onChange={(education) => set({ education })} addLabel="Adicionar formação"
        make={() => ({ course: "", institution: "", period: "", status: "", notes: "" })} itemLabel={(e) => e.course}
        render={(e, u) => (
          <div className="grid2">
            <TextField label="Curso" value={e.course} onChange={(v) => u({ course: v })} />
            <TextField label="Instituição" value={e.institution} onChange={(v) => u({ institution: v })} />
            <TextField label="Período / situação" value={e.period} onChange={(v) => u({ period: v })} hint="Ex.: Concluída em janeiro de 2026 | Em andamento" />
            <TextField label="Status (concluída / em andamento)" value={e.status} onChange={(v) => u({ status: v })} />
            <TextField label="Observações" value={e.notes} onChange={(v) => u({ notes: v })} />
          </div>
        )} />

      <fieldset className="group">
        <legend>Conquistas</legend>
        <LinesField label="Conquistas" value={profile.achievements} onChange={(achievements) => set({ achievements })} rows={4} />
      </fieldset>

      <Repeater title="Certificações" items={profile.certifications} onChange={(certifications) => set({ certifications })} addLabel="Adicionar certificação"
        make={() => ({ name: "", issuer: "" })} itemLabel={(c) => c.name}
        render={(c, u) => (
          <div className="grid2">
            <TextField label="Nome" value={c.name} onChange={(v) => u({ name: v })} />
            <TextField label="Emissor" value={c.issuer} onChange={(v) => u({ issuer: v })} />
          </div>
        )} />

      <Repeater title="Conhecimentos técnicos (categorias)" items={profile.skills} onChange={(skills) => set({ skills })} addLabel="Adicionar categoria"
        make={() => ({ name: "", items: [] })} itemLabel={(s) => s.name}
        render={(s, u) => (
          <>
            <TextField label="Categoria" value={s.name} onChange={(v) => u({ name: v })} />
            <LinesField label="Itens" value={s.items} onChange={(items) => u({ items })} rows={5}
              hint="Um por linha. Liste apenas o que você realmente conhece ou explorou; isto não declara proficiência avançada." />
          </>
        )} />

      <Repeater title="Projetos" items={profile.projects} onChange={(projects) => set({ projects })} addLabel="Adicionar projeto"
        make={() => ({ name: "", subtitle: "", description: "", technologies: [], bullets: [], link: "" })} itemLabel={(p) => p.name}
        render={(p, u) => (
          <>
            <div className="grid2">
              <TextField label="Nome" value={p.name} onChange={(v) => u({ name: v })} />
              <TextField label="Subtítulo" value={p.subtitle} onChange={(v) => u({ subtitle: v })} />
              <TextField label="Link (opcional)" value={p.link} onChange={(v) => u({ link: v })} />
            </div>
            <TextArea label="Descrição" value={p.description} onChange={(v) => u({ description: v })} rows={3} />
            <CsvField label="Tecnologias" value={p.technologies} onChange={(technologies) => u({ technologies })} />
            <LinesField label="Pontos de destaque" value={p.bullets} onChange={(bullets) => u({ bullets })} rows={4}
              hint="Um por linha. Não inclua métricas ou resultados que você não possa comprovar." />
          </>
        )} />

      <Repeater title="Experiência profissional (somente vínculos reais)" items={profile.experiences} onChange={(experiences) => set({ experiences })} addLabel="Adicionar experiência"
        make={() => ({ company: "", role: "", start: "", end: "", location: "", bullets: [] })} itemLabel={(x) => `${x.role} — ${x.company}`}
        render={(x, u) => (
          <>
            <div className="grid2">
              <TextField label="Empresa" value={x.company} onChange={(v) => u({ company: v })} />
              <TextField label="Cargo" value={x.role} onChange={(v) => u({ role: v })} />
              <TextField label="Início" value={x.start} onChange={(v) => u({ start: v })} placeholder="mm/aaaa" />
              <TextField label="Fim" value={x.end} onChange={(v) => u({ end: v })} placeholder="mm/aaaa ou Atual" />
              <TextField label="Local / modalidade" value={x.location} onChange={(v) => u({ location: v })} placeholder="Remoto" />
            </div>
            <LinesField label="Atividades" value={x.bullets} onChange={(bullets) => u({ bullets })} rows={4} />
          </>
        )} />

      <Repeater title="Idiomas" items={profile.languages} onChange={(languages) => set({ languages })} addLabel="Adicionar idioma"
        make={() => ({ name: "", level: "" })} itemLabel={(l) => l.name}
        render={(l, u) => (
          <div className="grid2">
            <TextField label="Idioma" value={l.name} onChange={(v) => u({ name: v })} />
            <TextField label="Nível" value={l.level} onChange={(v) => u({ level: v })} />
          </div>
        )} />

      <div className="sticky-bar">
        <button className="btn primary" onClick={save} disabled={saving}>{saving ? "Salvando…" : "Salvar perfil"}</button>
        <button className="btn ghost" onClick={reset}>Restaurar perfil inicial</button>
        <span role="status" className="ok">{msg}</span>
        {error && <span role="alert" className="err-inline">{error}</span>}
      </div>
    </main>
  );
}
