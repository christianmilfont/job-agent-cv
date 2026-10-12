import type { AppStatus, Application, ApplicationSummary, Profile, ResumeContent } from "./types";

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
  } catch { /* corpo não-JSON */ }
  return `Erro ${res.status}. Verifique se o servidor (backend) está em execução.`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...init });
  } catch {
    throw new Error("Não foi possível conectar ao servidor. Verifique se o backend está em execução na porta 8000.");
  }
  if (!res.ok) throw new Error(await parseError(res));
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const json = (method: string, body?: unknown): RequestInit => ({ method, body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  status: () => request<AppStatus>("/api/status"),
  getProfile: () => request<Profile>("/api/profile"),
  saveProfile: (p: Profile) => request<Profile>("/api/profile", json("PUT", p)),
  resetProfile: () => request<Profile>("/api/profile/reset", json("POST")),
  listApplications: () => request<ApplicationSummary[]>("/api/applications"),
  getApplication: (id: number) => request<Application>(`/api/applications/${id}`),
  createApplication: (job_description: string, company: string, role: string) =>
    request<Application>("/api/applications", json("POST", { job_description, company, role })),
  updateApplication: (id: number, data: { company?: string; role?: string; resume?: ResumeContent }) =>
    request<Application>(`/api/applications/${id}`, json("PUT", data)),
  restore: (id: number) => request<Application>(`/api/applications/${id}/restore`, json("POST")),
  remove: (id: number) => request<void>(`/api/applications/${id}`, json("DELETE")),
  /** Renderiza o conteúdo atual (mesmo não salvo) e devolve o arquivo. */
  async exportFile(fmt: "pdf" | "docx", resume: ResumeContent): Promise<{ blob: Blob; filename: string }> {
    let res: Response;
    try {
      res = await fetch(`/api/export/${fmt}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(resume) });
    } catch {
      throw new Error("Não foi possível conectar ao servidor.");
    }
    if (!res.ok) throw new Error(await parseError(res));
    const m = /filename="([^"]+)"/.exec(res.headers.get("Content-Disposition") ?? "");
    return { blob: await res.blob(), filename: m?.[1] ?? `curriculo.${fmt}` };
  },
};

export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
