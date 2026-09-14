import { FormEvent, useState } from "react";

interface Props {
  onSubmit: (question: string) => void;
  loading: boolean;
}

export default function QueryBox({ onSubmit, loading }: Props) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!value.trim() || loading) return;
    onSubmit(value.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ej: ¿Qué debo hacer si se presenta una situación de convivencia escolar?"
        className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-institutional"
      />
      <button
        type="submit"
        disabled={loading}
        className="rounded-lg bg-institutional px-6 py-3 text-sm font-medium text-white hover:bg-institutional-dark disabled:opacity-50"
      >
        {loading ? "Consultando..." : "Consultar"}
      </button>
    </form>
  );
}
