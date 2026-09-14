import { useState } from "react";
import { askQuestion } from "../api/client";
import AnswerCard from "../components/AnswerCard";
import History from "../components/History";
import QueryBox from "../components/QueryBox";
import type { QueryResponse } from "../types";

interface HistoryItem {
  question: string;
  response: QueryResponse;
}

export default function Home() {
  const [current, setCurrent] = useState<HistoryItem | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(question: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await askQuestion(question);
      const item = { question, response };
      setCurrent(item);
      setHistory((prev) => [item, ...prev].slice(0, 20));
    } catch {
      setError("Ocurrió un error al procesar la consulta. Intenta nuevamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto grid max-w-5xl grid-cols-1 gap-8 px-6 py-10 md:grid-cols-[1fr_260px]">
      <div className="space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold text-slate-900">
            Asistente Virtual de la Secretaría de Educación
          </h1>
          <p className="text-slate-600">
            Consulta resoluciones, circulares, protocolos, lineamientos y demás
            documentación institucional. Realiza tu pregunta en lenguaje natural y te
            mostraremos la información encontrada junto con sus fuentes.
          </p>
        </header>

        <QueryBox onSubmit={handleSubmit} loading={loading} />

        {error && <p className="text-sm text-red-600">{error}</p>}
        {current && <AnswerCard response={current.response} />}
      </div>

      <aside>
        <History items={history} onSelect={setCurrent} />
      </aside>
    </div>
  );
}
