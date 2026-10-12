import { useEffect, useState } from "react";
import { api } from "./api";
import type { AppStatus, ApplicationSummary } from "./types";

const fmtDate = (iso: string) => new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

export default function Dashboard({ onOpen, onProfile }: { onOpen: (id: number) => void; onProfile: () => void }) {
  const [job, setJob] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<ApplicationSummary[] | null>(null);
  const [status, setStatus] = useState<AppStatus | null>(null);

  const load = () => api.listApplications().then(setHistory).catch((e) => { setHistory([]); setError(e.message); });
  useEffect(() => { load(); api.status().then(setStatus).catch(() => undefined); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (job.trim().length < 40) { setError("Cole a descrição completa da vaga (mínimo de 40 caracteres)."); return; }
    setBusy(true);
    try {
      const app = await api.createApplication(job, company, role);
      onOpen(app.id);
    } catch (err) { setError((err as Error).message); }
    finally { setBusy(false); }
  }

  async function remove(id: number) {
    if (!window.confirm("Excluir esta candidatura? Esta ação não pode ser desfeita.")) return;
    try { await api.remove(id); load(); } catch (e) { setError((e as Error).message); }
  }

  return (
    <main className="container">
      <header className="topbar">
        <div>
          <h1>Job Agent CV</h1>
          <p className="lead">Currículos sob medida para cada vaga, a partir do seu perfil real.</p>
        </div>
        <button className="btn" onClick={onProfile}>Editar perfil profissional</button>
      </header>

      {status && (
        <p className={`alert ${status.ai_enabled ? "info" : "warn"}`} role="status">
          <strong>{status.ai_enabled ? "Modo IA ativo." : "Modo sem IA (regras e modelos)."}</strong> {status.message}
        </p>
      )}

      <form className="card" onSubmit={submit}>
        <label htmlFor="job" className="big-label">Descrição da vaga</label>
        <textarea id="job" className="job-input" rows={12} value={job} onChange={(e) => setJob(e.target.value)}
          placeholder="Cole aqui o texto completo da vaga: responsabilidades, requisitos, diferenciais…" disabled={busy} />
        <div className="grid2">
          <div className="field"><label htmlFor="company">Empresa (opcional)</label>
            <input id="company" value={company} onChange={(e) => setCompany(e.target.value)} disabled={busy} /></div>
          <div className="field"><label htmlFor="role">Cargo (opcional)</label>
            <input id="role" value={role} onChange={(e) => setRole(e.target.value)} disabled={busy} /></div>
        </div>
        {error && <p className="alert error" role="alert">{error}</p>}
        <button className="btn primary large" type="submit" disabled={busy} aria-busy={busy}>
          {busy ? "Analisando a vaga…" : "Analisar vaga e gerar currículo"}
        </button>
      </form>

      <section aria-labelledby="hist">
        <h2 id="hist">Histórico de candidaturas</h2>
        {history === null && <p aria-busy="true">Carregando…</p>}
        {history?.length === 0 && <p className="empty">Nenhuma candidatura ainda. Cole uma vaga acima para começar.</p>}
        {!!history?.length && (
          <ul className="history">
            {history.map((h) => (
              <li key={h.id}>
                <button className="history-open" onClick={() => onOpen(h.id)}>
                  <span className={`score-pill ${h.score >= 70 ? "good" : h.score >= 45 ? "mid" : "low"}`} aria-label={`Score ${h.score}`}>{h.score}</span>
                  <span className="history-text">
                    <strong>{h.role || "Cargo não identificado"}</strong>
                    <small>{h.company || "Empresa não informada"} · {fmtDate(h.created_at)} · {h.mode === "llm" ? "com IA" : "sem IA"}</small>
                  </span>
                </button>
                <button className="btn small danger" onClick={() => remove(h.id)} aria-label={`Excluir ${h.role}`}>Excluir</button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
