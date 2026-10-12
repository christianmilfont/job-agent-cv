import { useId, type ReactNode } from "react";

interface FieldProps { label: string; value: string; onChange: (v: string) => void; hint?: string; placeholder?: string; type?: string }

export function TextField({ label, value, onChange, hint, placeholder, type = "text" }: FieldProps) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input id={id} type={type} value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
      {hint && <small>{hint}</small>}
    </div>
  );
}

export function TextArea({ label, value, onChange, hint, rows = 4, placeholder }: Omit<FieldProps, "type"> & { rows?: number }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <textarea id={id} rows={rows} value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
      {hint && <small>{hint}</small>}
    </div>
  );
}

/** Lista de textos editada como uma linha por item. */
export function LinesField({ label, value, onChange, hint, rows = 4 }: { label: string; value: string[]; onChange: (v: string[]) => void; hint?: string; rows?: number }) {
  return <TextArea label={label} value={value.join("\n")} rows={rows} hint={hint ?? "Um item por linha."} onChange={(v) => onChange(v.split("\n"))} />;
}

export function CsvField({ label, value, onChange, hint }: { label: string; value: string[]; onChange: (v: string[]) => void; hint?: string }) {
  return <TextField label={label} value={value.join(", ")} hint={hint ?? "Separe por vírgulas."} onChange={(v) => onChange(v.split(","))} />;
}

export const clean = (xs: string[]) => xs.map((x) => x.trim()).filter(Boolean);

export function Repeater<T>({ title, items, onChange, make, render, itemLabel, addLabel }: {
  title: string; items: T[]; onChange: (items: T[]) => void; make: () => T;
  render: (item: T, update: (patch: Partial<T>) => void) => ReactNode; itemLabel: (item: T, i: number) => string; addLabel: string;
}) {
  const move = (i: number, d: number) => {
    const j = i + d;
    if (j < 0 || j >= items.length) return;
    const next = [...items];
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  };
  return (
    <fieldset className="group">
      <legend>{title}</legend>
      {items.length === 0 && <p className="empty">Nenhum item cadastrado.</p>}
      {items.map((it, i) => (
        <div className="repeat-item" key={i}>
          <div className="repeat-head">
            <strong>{itemLabel(it, i) || `Item ${i + 1}`}</strong>
            <span className="row-actions">
              <button type="button" className="btn small ghost" onClick={() => move(i, -1)} disabled={i === 0} aria-label="Mover para cima">↑</button>
              <button type="button" className="btn small ghost" onClick={() => move(i, 1)} disabled={i === items.length - 1} aria-label="Mover para baixo">↓</button>
              <button type="button" className="btn small danger" onClick={() => onChange(items.filter((_, k) => k !== i))}>Remover</button>
            </span>
          </div>
          {render(it, (patch) => onChange(items.map((x, k) => (k === i ? { ...x, ...patch } : x))))}
        </div>
      ))}
      <button type="button" className="btn small" onClick={() => onChange([...items, make()])}>+ {addLabel}</button>
    </fieldset>
  );
}
