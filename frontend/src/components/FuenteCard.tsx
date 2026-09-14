import { Fuente } from "../api/client";

const VIGENCIA_LABEL: Record<string, string> = {
  vigente: "Vigente",
  derogado: "Derogado",
  reemplazado: "Reemplazado",
  modificado: "Modificado",
  en_revision: "En revisión",
  desconocido: "Vigencia no determinada",
};

const VIGENCIA_STYLE: Record<string, string> = {
  vigente: "bg-emerald-50 text-emerald-800 border-emerald-200",
  derogado: "bg-red-50 text-red-800 border-red-200",
  reemplazado: "bg-amber-50 text-amber-800 border-amber-200",
  modificado: "bg-amber-50 text-amber-800 border-amber-200",
  en_revision: "bg-institucional-100 text-institucional-800 border-institucional-100",
  desconocido: "bg-institucional-50 text-institucional-700 border-institucional-100",
};

export default function FuenteCard({ fuente }: { fuente: Fuente }) {
  const ubicacion = [
    fuente.apartado ? `Apartado ${fuente.apartado}` : null,
    fuente.articulo,
    fuente.pagina ? `Página ${fuente.pagina}` : null,
  ]
    .filter(Boolean)
    .join(" — ");

  return (
    <div className="rounded-md border border-institucional-100 bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-institucional-950">{fuente.documento_nombre}</p>
          <p className="text-xs text-institucional-700">
            {[fuente.tipo_documento, fuente.numero && `N.º ${fuente.numero}`, fuente.anio]
              .filter(Boolean)
              .join(" · ")}
          </p>
          {ubicacion && <p className="mt-1 text-xs text-institucional-700">{ubicacion}</p>}
        </div>
        <span
          className={`shrink-0 rounded-full border px-2 py-0.5 text-xs ${
            VIGENCIA_STYLE[fuente.estado_vigencia] ?? VIGENCIA_STYLE.desconocido
          }`}
        >
          {VIGENCIA_LABEL[fuente.estado_vigencia] ?? fuente.estado_vigencia}
        </span>
      </div>
      {fuente.url_original && (
        <a
          href={fuente.url_original}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-xs text-institucional-700 underline decoration-institucional-700/40 underline-offset-2 hover:text-institucional-900"
        >
          Abrir documento original
        </a>
      )}
    </div>
  );
}
