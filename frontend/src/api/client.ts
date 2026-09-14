import type { DocumentItem, QueryResponse } from "../types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    throw new Error(`Error ${res.status}: ${await res.text()}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function askQuestion(question: string): Promise<QueryResponse> {
  return request<QueryResponse>("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function sendFeedback(interactionId: string, rating: number) {
  return request(`/query/${interactionId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating }),
  });
}

export function listDocuments(): Promise<DocumentItem[]> {
  return request<DocumentItem[]>("/documents");
}

export function uploadDocument(form: FormData): Promise<DocumentItem> {
  return request<DocumentItem>("/documents", { method: "POST", body: form });
}

export function updateDocument(id: string, payload: Record<string, unknown>): Promise<DocumentItem> {
  return request<DocumentItem>(`/documents/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteDocument(id: string): Promise<void> {
  return request<void>(`/documents/${id}`, { method: "DELETE" });
}

export interface Stats {
  total_documents: number;
  documents_indexed: number;
  documents_pending: number;
  total_queries: number;
  queries_today: number;
  unanswered_queries: number;
  avg_response_time_ms: number;
  avg_rating: number | null;
}

export function getStats(): Promise<Stats> {
  return request<Stats>("/admin/stats");
}

export interface DriveSyncResult {
  total_seen: number;
  created: number;
  updated: number;
  unchanged: number;
  skipped: number;
}

export function syncDrive(): Promise<DriveSyncResult> {
  return request<DriveSyncResult>("/admin/drive/sync", { method: "POST" });
}
