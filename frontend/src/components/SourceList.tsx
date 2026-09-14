import type { Source } from "../types";

const STATUS_LABEL: Record<string, string> = {
  vigente: "Vigente",
  derogado: "Derogado",
  reemplazado: "Reemplazado",
  modificado: "Modificado",
  en_revision: "En revisión",
  desconocido: "Estado no determinado",
};

const STATUS_COLOR: Record<string, string> = {
  vigente: "bg-emerald-100 text-emerald-700",
  derogado: "bg-red-100 text-red-700",
  reemplazado: "bg-amber-100 text-amber-700",
  modificado: "bg-amber-100 text-amber-700",
  en_revision: "bg-slate-100 text-slate-700",
  desconocido: "bg-slate-100 text-slate-700",
};

export default function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-700">Fuentes</h3>
      {sources.map((s, i) => (
        <div key={i} className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium text-slate-800">
              {s.doc_type} {s.number ? `N.º ${s.number}` : ""} {s.year ? `de ${s.year}` : ""}
            </span>
            <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_COLOR[s.status] ?? STATUS_COLOR.desconocido}`}>
              {STATUS_LABEL[s.status] ?? s.status}
            </span>
          </div>
          <p className="mt-1 text-slate-600">{s.document_title}</p>
          <p className="mt-1 text-xs text-slate-500">
            {[
              s.section && `Apartado ${s.section}`,
              s.article && `Artículo ${s.article}`,
              s.numeral && `Numeral ${s.numeral}`,
              s.page && `Página ${s.page}`,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
          <p className="mt-2 italic text-slate-500">&quot;{s.excerpt}&quot;</p>
          {s.source_url && (
            <a
              href={s.source_url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-institutional hover:underline"
            >
              Abrir documento original
            </a>
          )}
        </div>
      ))}
    </div>
  );
}
