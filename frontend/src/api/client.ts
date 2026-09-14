const TOKEN_KEY = "sec_edu_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`/api${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Sesión expirada");
  }

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || "Error en la solicitud");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; role: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ id: string; email: string; full_name: string | null; role: string }>("/auth/me"),

  query: (pregunta: string) =>
    request<ChatResponse>("/chat/query", { method: "POST", body: JSON.stringify({ pregunta }) }),
  history: () => request<HistoryItem[]>("/chat/history"),
  rate: (queryLogId: string, valoracion: number) =>
    request(`/chat/${queryLogId}/rating`, { method: "POST", body: JSON.stringify({ valoracion }) }),

  listDocuments: () => request<DocumentItem[]>("/documents"),
  uploadDocument: (formData: FormData) =>
    request<DocumentItem>("/documents/upload", { method: "POST", body: formData }),
  deleteDocument: (id: string) => request(`/documents/${id}`, { method: "DELETE" }),
  reprocessDocument: (id: string) => request<DocumentItem>(`/documents/${id}/process`, { method: "POST" }),
  updateDocumentMetadata: (id: string, payload: Partial<DocumentItem>) =>
    request<DocumentItem>(`/documents/${id}/metadata`, { method: "PATCH", body: JSON.stringify(payload) }),

  statistics: () => request<Statistics>("/admin/statistics"),
  audit: () => request<AuditItem[]>("/admin/audit"),
};

export interface Fuente {
  documento_nombre: string;
  tipo_documento: string | null;
  numero: string | null;
  anio: number | null;
  estado_vigencia: string;
  pagina: number | null;
  apartado: string | null;
  articulo: string | null;
  chunk_id: string;
  url_original: string | null;
}

export interface ChatResponse {
  respondido: boolean;
  respuesta: string;
  fuentes: Fuente[];
  nivel_confianza: string;
  posible_contradiccion: boolean;
  query_log_id: string;
}

export interface HistoryItem {
  id: string;
  pregunta: string;
  respuesta: string;
  respondido: boolean;
  creado_en: string;
}

export interface DocumentItem {
  id: string;
  nombre: string;
  tipo_documento: string | null;
  numero: string | null;
  anio: number | null;
  tema: string | null;
  estado_vigencia: string;
  estado_procesamiento: string;
  requirio_ocr: boolean;
  formato: string;
  es_demo: boolean;
  fecha_carga: string;
  fecha_actualizacion: string;
}

export interface Statistics {
  total_documentos: number;
  documentos_procesados: number;
  documentos_pendientes: number;
  documentos_error: number;
  total_consultas: number;
  consultas_sin_respuesta: number;
  tiempo_promedio_respuesta_ms: number | null;
}

export interface AuditItem {
  id: string;
  usuario_id: string | null;
  fecha: string;
  pregunta: string;
  chunks_recuperados: string[] | null;
  respondido: boolean;
  nivel_confianza: string | null;
  modelo_utilizado: string | null;
  tiempo_respuesta_ms: number | null;
}
