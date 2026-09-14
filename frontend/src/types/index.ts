export interface Source {
  document_id: string;
  document_title: string;
  doc_type: string;
  number: string | null;
  year: number | null;
  issue_date: string | null;
  status: string;
  page: number | null;
  article: string | null;
  numeral: string | null;
  section: string | null;
  source_url: string | null;
  excerpt: string;
}

export interface QueryResponse {
  answer: string;
  confidence: "encontrada" | "inferida" | "no_disponible";
  sources: Source[];
  warning: string | null;
  interaction_id: string;
}

export interface DocumentItem {
  id: string;
  title: string;
  doc_type: string;
  number: string | null;
  issue_date: string | null;
  year: number | null;
  issuing_entity: string | null;
  dependency: string | null;
  category_id: string | null;
  version: string | null;
  status: string;
  source_url: string | null;
  indexing_status: string;
  source: string;
  uploaded_at: string;
  updated_at: string;
}
