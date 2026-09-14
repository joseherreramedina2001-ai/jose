import { FormEvent, useEffect, useState } from "react";
import { deleteDocument, getStats, listDocuments, Stats, updateDocument, uploadDocument } from "../api/client";
import type { DocumentItem } from "../types";

const DOC_TYPES = [
  "resolucion",
  "circular",
  "decreto",
  "acuerdo",
  "protocolo",
  "manual",
  "lineamiento",
  "guia",
  "directiva",
  "concepto",
  "procedimiento",
  "reglamento",
  "otro",
];

const STATUSES = ["vigente", "derogado", "reemplazado", "modificado", "en_revision", "desconocido"];

export default function Admin() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [title, setTitle] = useState("");
  const [docType, setDocType] = useState(DOC_TYPES[0]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  async function refresh() {
    const [docs, s] = await Promise.all([listDocuments(), getStats()]);
    setDocuments(docs);
    setStats(s);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    if (!file || !title) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    form.append("title", title);
    form.append("doc_type", docType);
    try {
      await uploadDocument(form);
      setTitle("");
      setFile(null);
      await refresh();
    } finally {
      setUploading(false);
    }
  }

  async function handleStatusChange(id: string, status: string) {
    await updateDocument(id, { status });
    await refresh();
  }

  async function handleDelete(id: string) {
    await deleteDocument(id);
    await refresh();
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-6 py-10">
      <h1 className="text-2xl font-semibold text-slate-900">Panel administrativo</h1>

      {stats && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Stat label="Documentos" value={stats.total_documents} />
          <Stat label="Indexados" value={stats.documents_indexed} />
          <Stat label="Pendientes" value={stats.documents_pending} />
          <Stat label="Consultas" value={stats.total_queries} />
          <Stat label="Consultas hoy" value={stats.queries_today} />
          <Stat label="Sin respuesta" value={stats.unanswered_queries} />
          <Stat label="Tiempo prom. (ms)" value={Math.round(stats.avg_response_time_ms)} />
          <Stat label="Satisfacción prom." value={stats.avg_rating ? stats.avg_rating.toFixed(1) : "-"} />
        </div>
      )}

      <form onSubmit={handleUpload} className="space-y-3 rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-sm font-semibold text-slate-700">Cargar documento</h2>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Título del documento"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {DOC_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm"
        />
        <button
          type="submit"
          disabled={uploading}
          className="rounded-lg bg-institutional px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {uploading ? "Subiendo..." : "Subir e indexar"}
        </button>
      </form>

      <div className="space-y-2">
        <h2 className="text-sm font-semibold text-slate-700">Documentos</h2>
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-2">Título</th>
                <th className="px-4 py-2">Tipo</th>
                <th className="px-4 py-2">Indexación</th>
                <th className="px-4 py-2">Vigencia</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {documents.map((d) => (
                <tr key={d.id} className="border-t border-slate-100">
                  <td className="px-4 py-2">{d.title}</td>
                  <td className="px-4 py-2">{d.doc_type}</td>
                  <td className="px-4 py-2">{d.indexing_status}</td>
                  <td className="px-4 py-2">
                    <select
                      value={d.status}
                      onChange={(e) => handleStatusChange(d.id, e.target.value)}
                      className="rounded border border-slate-300 px-2 py-1 text-xs"
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button onClick={() => handleDelete(d.id)} className="text-red-600 hover:underline">
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}
