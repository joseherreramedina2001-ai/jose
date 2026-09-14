import { useState } from "react";
import { sendFeedback } from "../api/client";
import type { QueryResponse } from "../types";
import SourceList from "./SourceList";

const CONFIDENCE_LABEL: Record<string, string> = {
  encontrada: "Información encontrada directamente en la documentación",
  inferida: "Información inferida a partir de la documentación",
  no_disponible: "Sin información suficiente",
};

export default function AnswerCard({ response }: { response: QueryResponse }) {
  const [rated, setRated] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(response.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  async function handleRate(rating: number) {
    await sendFeedback(response.interaction_id, rating);
    setRated(true);
  }

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <span className="inline-block rounded-full bg-institutional/10 px-3 py-1 text-xs font-medium text-institutional">
        {CONFIDENCE_LABEL[response.confidence]}
      </span>

      {response.warning && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          {response.warning}
        </div>
      )}

      <p className="whitespace-pre-wrap text-slate-800">{response.answer}</p>

      <div className="flex items-center gap-4 text-xs text-slate-500">
        <button onClick={handleCopy} className="hover:text-institutional">
          {copied ? "Copiado" : "Copiar respuesta"}
        </button>
        {!rated ? (
          <span className="flex items-center gap-2">
            ¿Fue útil?
            <button onClick={() => handleRate(5)} className="hover:text-institutional">
              Sí
            </button>
            <button onClick={() => handleRate(1)} className="hover:text-institutional">
              No
            </button>
          </span>
        ) : (
          <span>Gracias por tu valoración</span>
        )}
      </div>

      <SourceList sources={response.sources} />
    </div>
  );
}
