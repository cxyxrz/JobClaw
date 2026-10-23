import { getToken } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  code: number;
  status: number;

  constructor(code: number, status: number, message: string) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export interface UserOut {
  id: number;
  username: string;
  role: string;
  vip_level: number;
  vip_expires_at: string | null;
}

export interface LoginData {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserOut;
}

export interface PingData {
  pong: boolean;
  role: string;
}

interface ApiOptions extends Omit<RequestInit, "headers"> {
  /** Attach the bearer token (default true). */
  auth?: boolean;
}

interface Envelope<T> {
  code: number;
  message: string;
  data: T;
  trace_id: string;
}

export interface JobOut {
  id: number;
  title: string;
  company: string;
  city: string;
  batch: string;
  category: string | null;
  salary_text: string | null;
  description: string;
  source_url: string | null;
  status: string;
  published_at: string;
}

export interface JobPage {
  items: JobOut[];
  total: number;
  page: number;
  page_size: number;
}

export interface DictItemOut {
  id: number;
  item_key: string;
  item_value: string;
  sort_order: number;
  enabled: boolean;
}

export interface DictTypeOut {
  type_code: string;
  name: string;
  version: number;
  description: string | null;
  items: DictItemOut[];
}

export interface DictSnapshot {
  version: number;
  types: DictTypeOut[];
}

export interface JobQuery {
  city?: string;
  batch?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}

export async function fetchJobs(query: JobQuery = {}): Promise<JobPage> {
  const params = new URLSearchParams();
  if (query.city) params.set("city", query.city);
  if (query.batch) params.set("batch", query.batch);
  if (query.keyword) params.set("keyword", query.keyword);
  if (query.page) params.set("page", String(query.page));
  if (query.page_size) params.set("page_size", String(query.page_size));
  const qs = params.toString();
  return api<JobPage>(`/api/v1/jobs${qs ? `?${qs}` : ""}`);
}

/** Fetch the dict snapshot; honors the version param and reports 304 Not Modified. */
export async function fetchDicts(
  version?: number,
): Promise<{ notModified: boolean; snapshot?: DictSnapshot }> {
  const res = await fetch(
    `${API_BASE}/api/v1/dicts${version != null ? `?version=${version}` : ""}`,
  );
  if (res.status === 304) return { notModified: true };
  const body = (await res.json()) as Envelope<DictSnapshot>;
  if (!res.ok || body.code !== 0) {
    throw new ApiError(
      body?.code ?? res.status * 100,
      res.status,
      body?.message ?? res.statusText,
    );
  }
  return { notModified: false, snapshot: body.data };
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { auth = true, ...init } = options;
  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  const token = auth ? getToken() : null;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  let body: Envelope<T> | null = null;
  try {
    body = (await res.json()) as Envelope<T>;
  } catch {
    body = null;
  }
  if (!res.ok || !body || body.code !== 0) {
    throw new ApiError(
      body?.code ?? res.status * 100,
      res.status,
      body?.message ?? res.statusText,
    );
  }
  return body.data;
}

/* ---------------- M2 采集与草稿 ---------------- */

export interface CollectResult {
  draft_id: number | null;
  status: string;
  confidence: number;
  title: string | null;
  company: string | null;
  message: string;
}

export interface DraftOut {
  id: number;
  title: string | null;
  company: string | null;
  city: string | null;
  batch: string | null;
  category: string | null;
  salary_text: string | null;
  description: string;
  source_url: string | null;
  source_type: string;
  confidence: number;
  status: string;
  review_note: string | null;
  created_at: string;
}

export interface DraftPage {
  items: DraftOut[];
  total: number;
  page: number;
  page_size: number;
}

export async function submitCollect(
  source_type: string,
  content: string,
): Promise<CollectResult> {
  return api<CollectResult>("/api/v1/collect", {
    method: "POST",
    body: JSON.stringify({ source_type, content }),
  });
}

export async function submitCollectFile(
  source_type: "excel" | "image",
  file: File,
): Promise<CollectResult> {
  const form = new FormData();
  form.append("source_type", source_type);
  form.append("file", file);
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}/api/v1/collect/upload`, {
    method: "POST",
    headers,
    body: form,
  });
  const body = (await res.json()) as Envelope<CollectResult>;
  if (!res.ok || body.code !== 0) {
    throw new ApiError(body.code, res.status, body.message);
  }
  return body.data;
}

export async function fetchDrafts(
  status?: string,
  page = 1,
  page_size = 20,
): Promise<DraftPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(page_size) });
  if (status) params.set("status", status);
  return api<DraftPage>(`/api/v1/admin/drafts?${params}`);
}

export async function reviewDraft(
  id: number,
  action: "accept" | "reject",
  note?: string,
): Promise<DraftOut> {
  return api<DraftOut>(`/api/v1/admin/drafts/${id}/review`, {
    method: "POST",
    body: JSON.stringify({ action, note }),
  });
}
