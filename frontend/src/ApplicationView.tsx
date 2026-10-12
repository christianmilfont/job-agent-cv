import { useEffect, useMemo, useRef, useState } from "react";
import { api, saveBlob } from "./api";
import { clean } from "./fields";
import ResumeEditor from "./ResumeEditor";
import ResumePreview from "./ResumePreview";
import type { Application, MatchItem, ResumeContent } from "./types";

type Tab = "overview" | "requirements" | "resume" | "export";
const TABS: [Tab, string][] = [["overview", "Visão geral"], ["requirements", "Requisitos"], ["resume", "Currículo"], ["export", "Exportar"]];

const cleanResume = (r: ResumeContent): ResumeContent => ({
  ...r,
  contacts: clean(r.contacts),
  links: r.links.filter((l) => l.url.trim()).map((l) => ({ label: l.label.trim() || l.url.trim(), url: l.url.trim() })),
  skills: r.skills.map((g) => ({ category: g.category.trim(), items: clean(g.items) })).filter((g) => g.category && g.items.length),
  experience: r.experience.map((e) => ({ ...e, bullets: clean(e.bullets) })).filter((e) => e.role.trim() || e.company.trim()),
  projects: r.projects.map((p) => ({ ...p, bullets: clean(p.bullets), technologies: clean(p.technologies) })).filter((p) => p.name.trim()),
  education: r.education.filter((e) => e.course.trim()),
  certifications: clean(r.certifications), achievements: clean(r.achievements), languages: clean(r.languages),
});

export default function ApplicationView({ id, onBack }: { id: number; onBack: () => void }) {
  const [app, setApp] = useState<Application | null>(null);
  const [resume, setResume] = useState<ResumeContent | null>(null);
  const [saved, setSaved] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [pdfUrl, setPdfUrl] = useState("");
  const [meta, setMeta] = useState({ company: "", role: "" });
  const pdfRef = useRef("");

  useEffect(() => {
    api.getApplication(id).then((a) => {
      setApp(a); setResume(a.resume); setSaved(JSON.stringify(a.resume)); setMeta({ company: a.company, role: a.role });
    }).catch((e) => setError(e.message));
    return () => { if (pdfRef.current) URL.revokeObjectURL(pdfRef.current); };
  }, [id]);

  const dirty = useMemo(() => !!resume && JSON.stringify(resume) !== saved || (!!app && (meta.company !== app.company || meta.role !== app.role)), [resume, saved, meta, app]);

  useEffect(() => {
    if (!dirty) return;
    const h = (e: BeforeUnloadEvent) => { e.preventDefault(); };
    window.addEventListener("beforeunload", h);
    return () => window.removeEventListener("beforeunload", h);
  }, [dirty]);

  if (!app || !resume) return <main className="container">{error ? <><p className="alert error" role="alert">{error}</p><button className="btn" onClick={onBack}>Voltar</button></> : <p aria-busy="true">Carregando candidatura…</p>}</main>;

  async function save(): Promise<ResumeContent | null> {
    setBusy("save"); setError("");
    try {
      const cleaned = cleanResume(resume!);
      const updated = await api.updateApplication(id, { resume: cleaned, company: meta.company, role: meta.role });
      setApp(updated); setResume(updated.resume); setSaved(JSON.stringify(updated.resume));
      return updated.resume;
    } catch (e) { setError((e as Error).message); return null; }
    finally { setBusy(""); }
  }

  async function download(fmt: "pdf" | "docx") {
    setBusy(fmt); setError("");
    try {
      const current = dirty ? await save() : resume!;
      if (!current) return;
      const { blob, filename } = await api.exportFile(fmt, current);
      saveBlob(blob, filename);
    } catch (e) { setError((e as Error).message); } finally { setBusy(""); }
  }

  async function refreshPdf() {
    setBusy("preview"); setError("");
    try {
      const { blob } = await api.exportFile("pdf", cleanResume(resume!));
      if (pdfRef.current) URL.revokeObjectURL(pdfRef.current);
      pdfRef.current = URL.createObjectURL(blob);
      setPdfUrl(pdfRef.current);
    } catch (e) { setError((e as Error).message); } finally { setBusy(""); }
  }

  async function restore() {
    if (!window.confirm("Descartar suas edições e voltar ao currículo gerado originalmente?")) return;
    setBusy("restore");
    try { const a = await api.restore(id); setApp(a); setResume(a.resume); setSaved(JSON.stringify(a.resume)); } catch (e) { setError((e as Error).message); } finally { setBusy(""); }
  }

  const a = app.analysis;
  const scoreClass = a.score >= 70 ? "good" : a.score >= 45 ? "mid" : "low";

  return (
    <main className="container">
      <div className="page-head">
        <button className="btn ghost" onClick={() => { if (!dirty || window.confirm("Há alterações não salvas. Sair mesmo assim?")) onBack(); }}>← Início</button>
        <div className="grow">
          <h1>{meta.role || "Candidatura"}{meta.company && <span className="muted"> · {meta.company}</span>}</h1>
        </div>
        {dirty && <span className="badge warn">Alterações não salvas</span>}
        <button className="btn primary" onClick={save} disabled={!dirty || busy === "save"}>{busy === "save" ? "Salvando…" : "Salvar"}</button>
      </div>

      {a.notices.length > 0 && (
        <div className={`alert ${a.mode === "llm" ? "info" : "warn"}`} role="status">
          <strong>{a.mode === "llm" ? "Gerado com IA" : "Gerado sem IA (modo por regras)"}</strong>
          <ul>{a.notices.map((n, i) => <li key={i}>{n}</li>)}</ul>
        </div>
      )}
      {error && <p className="alert error" role="alert">{error}</p>}

      <div className="tabs" role="tablist">
        {TABS.map(([k, label]) => (
          <button key={k} role="tab" id={`tab-${k}`} aria-selected={tab === k} aria-controls="panel" className={tab === k ? "active" : ""} onClick={() => setTab(k)}>{label}</button>
        ))}
      </div>

      <div id="panel" role="tabpanel" aria-labelledby={`tab-${tab}`}>
        {tab === "overview" && (
          <div className="stack">
            <div className="card score-card">
              <div className={`score-ring ${scoreClass}`} role="img" aria-label={`Score de compatibilidade ${a.score} de 100`}><span>{a.score}</span><small>/100</small></div>
              <div>
                <h2>Compatibilidade estimada</h2>
                <p>{a.summary}</p>
              </div>
            </div>
            <div className="grid2">
              <div className="field"><label htmlFor="m-role">Cargo</label><input id="m-role" value={meta.role} onChange={(e) => setMeta({ ...meta, role: e.target.value })} /></div>
              <div className="field"><label htmlFor="m-co">Empresa</label><input id="m-co" value={meta.company} onChange={(e) => setMeta({ ...meta, company: e.target.value })} /></div>
            </div>
            <div className="card">
              <h3>Como o score foi calculado</h3>
              <table className="plain">
                <thead><tr><th>Critério</th><th>Pontos</th><th>Motivo</th></tr></thead>
                <tbody>{a.score_components.map((c) => <tr key={c.criterion}><td>{c.criterion}</td><td>{c.points}/{c.max_points}</td><td>{c.explanation}</td></tr>)}</tbody>
              </table>
              <p className="hint">Score = pontos obtidos ÷ pontos possíveis nos critérios aplicáveis. Ausência de informação no perfil não significa ausência de competência: complete o perfil para refinar o resultado.</p>
            </div>
            <div className="card">
              <h3>Resumo da vaga</h3>
              <dl className="facts">
                <dt>Senioridade</dt><dd>{a.job.seniority || "Não identificada"}</dd>
                <dt>Experiência exigida</dt><dd>{a.job.years_required ? `${a.job.years_required}+ anos` : "Não especificada"}</dd>
                <dt>Tecnologias</dt><dd>{[...a.job.technologies_required, ...a.job.technologies_desired].join(", ") || "Nenhuma reconhecida"}</dd>
                <dt>Competências comportamentais</dt><dd>{a.job.soft_skills.join(", ") || "Não identificadas"}</dd>
                <dt>Palavras-chave ATS</dt><dd>{a.job.keywords.join(", ") || "—"}</dd>
              </dl>
              {a.job.responsibilities.length > 0 && <><h4>Responsabilidades</h4><ul>{a.job.responsibilities.map((x, i) => <li key={i}>{x}</li>)}</ul></>}
            </div>
          </div>
        )}

        {tab === "requirements" && (
          <div className="cols3">
            <Column title="MATCH" cls="good" empty="Nenhum requisito técnico respaldado." items={a.match} />
            <Column title="GAPS" cls="mid" empty="Nenhuma lacuna encontrada." items={a.gaps} />
            <section className="card col risk">
              <h3><span className="tag low">RISKS</span></h3>
              {a.risks.length === 0 ? <p className="empty">Nenhum risco crítico identificado.</p> : <ul>{a.risks.map((r, i) => <li key={i}>{r}</li>)}</ul>}
            </section>
          </div>
        )}

        {tab === "resume" && (
          <div className="split">
            <div>
              <div className="toolbar">
                <h2>Editor</h2>
                <button className="btn small ghost" onClick={restore} disabled={busy === "restore"}>Restaurar versão gerada</button>
              </div>
              <ResumeEditor r={resume} onChange={setResume} />
            </div>
            <div className="sticky-preview">
              <h2>Pré-visualização</h2>
              <ResumePreview r={cleanResume(resume)} />
            </div>
          </div>
        )}

        {tab === "export" && (
          <div className="stack">
            <div className="card">
              <h2>Baixar currículo</h2>
              <p>Os arquivos são gerados a partir da versão editada acima (alterações pendentes são salvas antes). Texto selecionável, coluna única e links clicáveis, para boa leitura por ATS.</p>
              <div className="btn-row">
                <button className="btn primary" onClick={() => download("pdf")} disabled={!!busy}>{busy === "pdf" ? "Gerando PDF…" : "Baixar PDF"}</button>
                <button className="btn primary" onClick={() => download("docx")} disabled={!!busy}>{busy === "docx" ? "Gerando DOCX…" : "Baixar DOCX"}</button>
                <button className="btn" onClick={refreshPdf} disabled={!!busy}>{busy === "preview" ? "Gerando…" : "Pré-visualizar PDF"}</button>
              </div>
            </div>
            {pdfUrl ? <iframe className="pdf-frame" title="Pré-visualização do PDF" src={pdfUrl} /> : <p className="empty">Clique em “Pré-visualizar PDF” para ver o arquivo exatamente como será exportado.</p>}
          </div>
        )}
      </div>
    </main>
  );
}

function Column({ title, cls, items, empty }: { title: string; cls: string; items: MatchItem[]; empty: string }) {
  const group = (level: "required" | "desired", label: string) => {
    const xs = items.filter((i) => i.level === level);
    return xs.length ? (
      <><h4>{label}</h4><ul>{xs.map((i) => <li key={i.requirement}><strong>{i.requirement}</strong><small>{i.evidence}</small></li>)}</ul></>
    ) : null;
  };
  return (
    <section className="card col">
      <h3><span className={`tag ${cls}`}>{title}</span> <span className="muted">({items.length})</span></h3>
      {items.length === 0 ? <p className="empty">{empty}</p> : <>{group("required", "Obrigatórios")}{group("desired", "Desejáveis")}</>}
    </section>
  );
}
