import { FormEvent, useEffect, useState } from "react";
import { api, DocumentItem, Statistics } from "../api/client";

const ESTADO_LABEL: Record<string, string> = {
  pendiente: "Pendiente",
  procesando: "Procesando",
  procesado: "Procesado",
  error: "Error",
};

export default function Admin() {
  const [documentos, setDocumentos] = useState<DocumentItem[]>([]);
  const [stats, setStats] = useState<Statistics | null>(null);
  const [cargando, setCargando] = useState(true);
  const [subiendo, setSubiendo] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);

  async function cargarTodo() {
    setCargando(true);
    const [docs, s] = await Promise.all([api.listDocuments(), api.statistics()]);
    setDocumentos(docs);
    setStats(s);
    setCargando(false);
  }

  useEffect(() => {
    cargarTodo();
  }, []);

  async function handleUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMensaje(null);
    const form = e.currentTarget;
    const data = new FormData(form);

    setSubiendo(true);
    try {
      await api.uploadDocument(data);
      setMensaje("Documento cargado. Se está procesando en segundo plano.");
      form.reset();
      await cargarTodo();
    } catch (err) {
      setMensaje(err instanceof Error ? err.message : "Error al cargar el documento");
    } finally {
      setSubiendo(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("¿Eliminar este documento? Esta acción no se puede deshacer.")) return;
    await api.deleteDocument(id);
    await cargarTodo();
  }

  async function handleReprocess(id: string) {
    await api.reprocessDocument(id);
    await cargarTodo();
  }

  async function handleVigenciaChange(id: string, estado_vigencia: string) {
    await api.updateDocumentMetadata(id, { estado_vigencia } as Partial<DocumentItem>);
    await cargarTodo();
  }

  if (cargando) return <div className="p-6 text-sm text-institucional-700">Cargando panel administrativo…</div>;

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-6">
      <div>
        <h1 className="font-display text-xl font-semibold text-institucional-950">Panel administrativo</h1>
        <p className="text-sm text-institucional-700">Gestión documental, estadísticas y auditoría.</p>
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Documentos" value={stats.total_documentos} />
          <StatCard label="Procesados" value={stats.documentos_procesados} />
          <StatCard label="Pendientes/con error" value={stats.documentos_pendientes + stats.documentos_error} />
          <StatCard label="Consultas totales" value={stats.total_consultas} />
        </div>
      )}

      <section className="rounded-lg border border-institucional-100 bg-white p-5">
        <h2 className="mb-3 font-display text-lg font-semibold text-institucional-950">Cargar documento</h2>
        <form onSubmit={handleUpload} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <input name="file" type="file" accept=".pdf,.docx,.txt" required className="sm:col-span-2 text-sm" />
          <Field name="nombre" label="Nombre del documento" required />
          <Field name="tipo_documento" label="Tipo (resolución, circular…)" />
          <Field name="numero" label="Número" />
          <Field name="anio" label="Año" type="number" />
          <Field name="entidad_emisora" label="Entidad emisora" />
          <Field name="dependencia" label="Dependencia" />
          <Field name="tema" label="Tema / categoría" />
          <Field name="version" label="Versión" />
          <div>
            <label className="mb-1 block text-sm text-institucional-800">Estado de vigencia</label>
            <select name="estado_vigencia" defaultValue="desconocido" className="w-full rounded-md border border-institucional-100 px-3 py-2 text-sm">
              <option value="vigente">Vigente</option>
              <option value="derogado">Derogado</option>
              <option value="reemplazado">Reemplazado</option>
              <option value="modificado">Modificado</option>
              <option value="en_revision">En revisión</option>
              <option value="desconocido">Desconocido</option>
            </select>
          </div>
          <Field name="url_original" label="URL del documento original" />
          <label className="flex items-center gap-2 text-sm text-institucional-800 sm:col-span-2">
            <input type="checkbox" name="es_demo" value="true" />
            Marcar como documento DEMO (dato de prueba, no normativa real)
          </label>

          {mensaje && <p className="text-sm text-institucional-800 sm:col-span-2">{mensaje}</p>}

          <button
            type="submit"
            disabled={subiendo}
            className="sm:col-span-2 rounded-md bg-institucional-900 py-2 text-sm font-medium text-white hover:bg-institucional-800 disabled:opacity-60"
          >
            {subiendo ? "Cargando…" : "Cargar y procesar documento"}
          </button>
        </form>
      </section>

      <section className="rounded-lg border border-institucional-100 bg-white p-5">
        <h2 className="mb-3 font-display text-lg font-semibold text-institucional-950">Documentos</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-institucional-100 text-xs uppercase tracking-wide text-institucional-700">
                <th className="py-2 pr-3">Nombre</th>
                <th className="py-2 pr-3">Tema</th>
                <th className="py-2 pr-3">Vigencia</th>
                <th className="py-2 pr-3">Procesamiento</th>
                <th className="py-2 pr-3">OCR</th>
                <th className="py-2 pr-3" />
              </tr>
            </thead>
            <tbody>
              {documentos.map((d) => (
                <tr key={d.id} className="border-b border-institucional-50">
                  <td className="py-2 pr-3">
                    {d.nombre}
                    {d.es_demo && <span className="ml-2 rounded bg-acento-100 px-1.5 py-0.5 text-xs text-acento-600">DEMO</span>}
                  </td>
                  <td className="py-2 pr-3 text-institucional-700">{d.tema ?? "—"}</td>
                  <td className="py-2 pr-3">
                    <select
                      value={d.estado_vigencia}
                      onChange={(e) => handleVigenciaChange(d.id, e.target.value)}
                      className="rounded border border-institucional-100 px-2 py-1 text-xs"
                    >
                      <option value="vigente">Vigente</option>
                      <option value="derogado">Derogado</option>
                      <option value="reemplazado">Reemplazado</option>
                      <option value="modificado">Modificado</option>
                      <option value="en_revision">En revisión</option>
                      <option value="desconocido">Desconocido</option>
                    </select>
                  </td>
                  <td className="py-2 pr-3">{ESTADO_LABEL[d.estado_procesamiento] ?? d.estado_procesamiento}</td>
                  <td className="py-2 pr-3">{d.requirio_ocr ? "Sí" : "No"}</td>
                  <td className="py-2 pr-3 text-right">
                    <button onClick={() => handleReprocess(d.id)} className="mr-3 text-xs text-institucional-700 underline">
                      Reprocesar
                    </button>
                    <button onClick={() => handleDelete(d.id)} className="text-xs text-red-700 underline">
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
              {documentos.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-institucional-700">
                    Aún no se han cargado documentos.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-institucional-100 bg-white p-4">
      <p className="font-display text-2xl font-semibold text-institucional-950">{value}</p>
      <p className="text-xs text-institucional-700">{label}</p>
    </div>
  );
}

function Field({
  name,
  label,
  required,
  type = "text",
}: {
  name: string;
  label: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <div>
      <label htmlFor={name} className="mb-1 block text-sm text-institucional-800">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        required={required}
        className="w-full rounded-md border border-institucional-100 px-3 py-2 text-sm focus:border-institucional-700 focus:outline-none focus:ring-1 focus:ring-institucional-700"
      />
    </div>
  );
}
