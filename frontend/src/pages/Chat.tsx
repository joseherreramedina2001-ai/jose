import { FormEvent, useState } from "react";
import { api, ChatResponse } from "../api/client";
import FuenteCard from "../components/FuenteCard";

interface Turno {
  pregunta: string;
  respuesta?: ChatResponse;
  cargando: boolean;
}

const PREGUNTAS_SUGERIDAS = [
  "¿Qué procedimiento debe seguirse ante una situación de convivencia escolar Tipo II?",
  "¿Qué obligaciones tiene el rector frente a una situación de convivencia escolar?",
  "¿Qué requisitos establece la Secretaría para el proceso de matrícula?",
];

export default function Chat() {
  const [pregunta, setPregunta] = useState("");
  const [turnos, setTurnos] = useState<Turno[]>([]);

  async function enviarPregunta(texto: string) {
    if (!texto.trim()) return;
    const index = turnos.length;
    setTurnos((prev) => [...prev, { pregunta: texto, cargando: true }]);
    setPregunta("");

    try {
      const respuesta = await api.query(texto);
      setTurnos((prev) => {
        const copia = [...prev];
        copia[index] = { pregunta: texto, respuesta, cargando: false };
        return copia;
      });
    } catch (err) {
      setTurnos((prev) => {
        const copia = [...prev];
        copia[index] = {
          pregunta: texto,
          cargando: false,
          respuesta: {
            respondido: false,
            respuesta: err instanceof Error ? err.message : "Ocurrió un error al consultar.",
            fuentes: [],
            nivel_confianza: "ninguna",
            posible_contradiccion: false,
            query_log_id: "",
          },
        };
        return copia;
      });
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    enviarPregunta(pregunta);
  }

  async function valorar(queryLogId: string, valor: number) {
    if (!queryLogId) return;
    try {
      await api.rate(queryLogId, valor);
    } catch {
      /* no bloquear la UI si falla la valoración */
    }
  }

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col px-4 py-6">
      {turnos.length === 0 && (
        <div className="mb-8 rounded-lg border border-institucional-100 bg-white p-6">
          <h2 className="font-display text-xl font-semibold text-institucional-950">
            Asistente Virtual de la Secretaría de Educación
          </h2>
          <p className="mt-2 text-sm text-institucional-700">
            Consulta resoluciones, circulares, protocolos, lineamientos y demás documentación
            institucional. Realiza tu pregunta en lenguaje natural y te mostraremos la
            información encontrada junto con sus fuentes.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {PREGUNTAS_SUGERIDAS.map((p) => (
              <button
                key={p}
                onClick={() => enviarPregunta(p)}
                className="rounded-full border border-institucional-100 px-3 py-1.5 text-xs text-institucional-800 hover:border-institucional-700 hover:text-institucional-950"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex-1 space-y-6 overflow-y-auto">
        {turnos.map((turno, i) => (
          <div key={i} className="space-y-3">
            <div className="ml-auto max-w-[85%] rounded-lg bg-institucional-900 px-4 py-2 text-sm text-white">
              {turno.pregunta}
            </div>

            {turno.cargando && (
              <p className="text-sm text-institucional-700">Consultando documentación institucional…</p>
            )}

            {turno.respuesta && (
              <div className="max-w-[95%] rounded-lg border border-institucional-100 bg-white p-4">
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-xs font-medium uppercase tracking-wide text-institucional-700">
                    Respuesta encontrada
                  </span>
                  {turno.respuesta.nivel_confianza !== "ninguna" && (
                    <span className="rounded-full bg-institucional-50 px-2 py-0.5 text-xs text-institucional-700">
                      Coincidencia {turno.respuesta.nivel_confianza}
                    </span>
                  )}
                </div>

                {turno.respuesta.posible_contradiccion && (
                  <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                    Se encontraron disposiciones diferentes entre documentos. Verifica cuál se
                    encuentra actualmente vigente antes de aplicar esta información.
                  </div>
                )}

                <div className="whitespace-pre-wrap text-sm leading-relaxed text-institucional-950">
                  {turno.respuesta.respuesta}
                </div>

                {turno.respuesta.fuentes.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <p className="text-xs font-medium uppercase tracking-wide text-institucional-700">
                      Fuentes consultadas
                    </p>
                    {turno.respuesta.fuentes.map((f) => (
                      <FuenteCard key={f.chunk_id} fuente={f} />
                    ))}
                  </div>
                )}

                {turno.respuesta.respondido && (
                  <div className="mt-4 flex items-center justify-between border-t border-institucional-100 pt-3">
                    <p className="text-xs text-institucional-700">
                      Esta respuesta se basa en la documentación institucional disponible al
                      momento de la consulta. No reemplaza la asesoría jurídica o técnica de la
                      Secretaría de Educación.
                    </p>
                    <div className="flex shrink-0 gap-1 pl-3">
                      {[1, 2, 3, 4, 5].map((v) => (
                        <button
                          key={v}
                          onClick={() => valorar(turno.respuesta!.query_log_id, v)}
                          className="text-institucional-400 hover:text-acento-600"
                          aria-label={`Valorar con ${v} estrellas`}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-4 flex gap-2 border-t border-institucional-100 pt-4">
        <input
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          placeholder="Escribe tu consulta sobre normativa o documentación institucional…"
          className="flex-1 rounded-md border border-institucional-100 px-3 py-2 text-sm focus:border-institucional-700 focus:outline-none focus:ring-1 focus:ring-institucional-700"
        />
        <button
          type="submit"
          className="rounded-md bg-institucional-900 px-4 py-2 text-sm font-medium text-white hover:bg-institucional-800"
        >
          Consultar
        </button>
      </form>
    </div>
  );
}
