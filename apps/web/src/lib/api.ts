export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return (await res.json()) as T;
}

export interface Citation {
  unit_id: string;
  display: string;
  link: string;
}

export interface ChatSegment {
  text: string;
  label: "source_backed" | "outside_knowledge" | "not_covered";
  unit_ids: string[];
  citations: Citation[];
  check_source?: boolean;
  related_topics?: string[];
}
