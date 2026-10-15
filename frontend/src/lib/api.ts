// Centralised API service layer for the local SignaVerify Flask backend.
// Change the backend address with VITE_API_BASE_URL (defaults to localhost:5000).

export const API_BASE_URL: string =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:5000";

export const ACCEPTED_IMAGE_TYPES = ["image/png", "image/jpeg"];
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

export interface Health {
  status: "ok";
  dataset_available: boolean;
  total_writers: number;
  min_signatures: number;
}

export interface User {
  username: string;
  full_name: string;
  model_path: string | null;
  model_available: boolean;
  sample_count: number;
  created_at: string;
}

export interface Metrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  confusion_matrix: number[][];
}

export interface TrainResult {
  writer_id?: number;
  username?: string;
  model_file: string;
  metrics: Metrics;
}

export type JobStatus = "queued" | "running" | "completed" | "failed";

export interface Job {
  job_id: string;
  kind: "cedar" | "user";
  target: string;
  status: JobStatus;
  result?: TrainResult;
  error?: string;
}

export interface VerifyResult {
  prediction: "Genuine" | "Forged";
  confidence: number;
  probabilities: {
    genuine: number;
    forged: number;
  };
}

export interface ModelsInfo {
  cedar: { writer_id: number; available: boolean }[];
  users: { username: string; available: boolean }[];
}

export interface Verification {
  id: number;
  kind: "cedar" | "user";
  target: string;
  prediction: "Genuine" | "Forged";
  confidence: number;
  created_at: string;
}

export interface Stats {
  registered_users: number;
  verifications: number;
  genuine: number;
  forged: number;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;

  try {
    res = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new ApiError(
      `Cannot reach the SignaVerify backend at ${API_BASE_URL}. Start the local Flask API and try again.`,
    );
  }

  const body = await res.json().catch(() => null);

  if (!res.ok) {
    throw new ApiError(body?.error ?? `Request failed (${res.status})`, res.status);
  }

  return body as T;
}

const formWith = (entries: [string, string | Blob][]) => {
  const fd = new FormData();

  entries.forEach(([key, value]) => {
    fd.append(key, value);
  });

  return fd;
};

export const api = {
  health: () => request<Health>("/api/health"),

  stats: () => request<Stats>("/api/stats"),

  users: () => request<User[]>("/api/users"),

  models: () => request<ModelsInfo>("/api/models"),

  verifications: (limit = 10) => request<Verification[]>(`/api/verifications?limit=${limit}`),

  registerUser: (fullName: string, username: string, files: File[]) =>
    request<User>("/api/users", {
      method: "POST",
      body: formWith([
        ["full_name", fullName],
        ["username", username],
        ...files.map((file) => ["signatures", file] as [string, Blob]),
      ]),
    }),

  trainUser: (username: string) =>
    request<Job>(`/api/users/${encodeURIComponent(username)}/train`, { method: "POST" }),

  trainCedar: (writerId: number) =>
    request<Job>(`/api/cedar/${writerId}/train`, {
      method: "POST",
    }),

  job: (jobId: string) => request<Job>(`/api/jobs/${encodeURIComponent(jobId)}`),

  verifyUser: (username: string, file: File) =>
    request<VerifyResult>(`/api/users/${encodeURIComponent(username)}/verify`, {
      method: "POST",
      body: formWith([["signature", file]]),
    }),

  verifyCedar: (writerId: number, file: File) =>
    request<VerifyResult>(`/api/cedar/${writerId}/verify`, {
      method: "POST",
      body: formWith([["signature", file]]),
    }),
};

export function validateImage(file: File): string | null {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    return `${file.name}: only PNG or JPEG images are accepted.`;
  }

  if (file.size > MAX_IMAGE_BYTES) {
    return `${file.name}: larger than 5 MB.`;
  }

  return null;
}
