import type { Debate, DebateRequest, Estimate, EstimateSummary } from "@/types";

export interface Health {
  status: "ok";
  version: string;
  env: "dev" | "test" | "prod";
  llm_configured: boolean;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
}

export function describeDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return (detail as ValidationIssue[])
      .slice(0, 5)
      .map(({ loc, msg }) => {
        const where = loc.filter((part) => part !== "body").join(".");
        return where ? `${where}: ${msg}` : msg;
      })
      .join("\n");
  }

  return null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail =
      body && typeof body === "object" && "detail" in body ? describeDetail(body.detail) : null;

    throw new ApiError(
      response.status,
      detail ?? `${init?.method ?? "GET"} ${path} failed (${response.status})`,
    );
  }

  return (await response.json()) as T;
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  health: (signal?: AbortSignal) => request<Health>("/health", { signal }),

  samples: () => request<EstimateSummary[]>("/estimates/samples"),
  sample: (id: string) => request<Estimate>(`/estimates/samples/${encodeURIComponent(id)}`),
  preview: (estimate: unknown) => post<Estimate>("/estimates/preview", estimate),

  demos: () => request<string[]>("/debates/demos"),
  debates: () => request<Debate[]>("/debates"),
  debate: (id: string) => request<Debate>(`/debates/${encodeURIComponent(id)}`),
  startDebate: (body: DebateRequest) => post<Debate>("/debates", body),
  eventsUrl: (id: string) => `/api/debates/${encodeURIComponent(id)}/events`,
};
