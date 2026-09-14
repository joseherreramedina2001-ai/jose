import type { QueryResponse } from "../types";

interface Item {
  question: string;
  response: QueryResponse;
}

export default function History({ items, onSelect }: { items: Item[]; onSelect: (item: Item) => void }) {
  if (items.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-700">Historial</h3>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i}>
            <button
              onClick={() => onSelect(item)}
              className="w-full truncate rounded-lg px-3 py-2 text-left text-sm text-slate-600 hover:bg-slate-100"
            >
              {item.question}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
