import { appConfig } from "@/lib/config";

import type { ErrorResponse } from "./types";

type QueryValue = string | number | boolean | null | undefined;

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: Record<string, unknown>;

  constructor(message: string, status = 500, code?: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

type ApiRequestOptions = Omit<RequestInit, "body"> & {
  query?: Record<string, QueryValue>;
  body?: unknown;
};

function toApiQueryKey(key: string) {
  return key.replace(/[A-Z]/g, (match) => `_${match.toLowerCase()}`);
}

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const url = new URL(path, `${appConfig.apiBaseUrl}/`);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === null || value === undefined || value === "") {
        continue;
      }

      url.searchParams.set(toApiQueryKey(key), String(value));
    }
  }

  return url;
}

function toApiError(error: unknown) {
  if (error instanceof ApiError) {
    return error;
  }

  if (error instanceof Error) {
    return new ApiError(error.message);
  }

  return new ApiError("Unexpected API error");
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}) {
  const { query, body, headers, ...init } = options;
  const response = await fetch(buildUrl(path, query), {
    ...init,
    cache: init.cache ?? "no-store",
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...headers
    },
    body: body ? JSON.stringify(body) : undefined
  });

  if (!response.ok) {
    let payload: ErrorResponse | null = null;

    try {
      payload = (await response.json()) as ErrorResponse;
    } catch {
      payload = null;
    }

    throw new ApiError(
      payload?.error.message || `Request failed with status ${response.status}`,
      response.status,
      payload?.error.code,
      payload?.error.details
    );
  }

  return (await response.json()) as T;
}

export async function safeApiCall<T>(operation: () => Promise<T>) {
  try {
    const data = await operation();
    return { data, error: null as ApiError | null };
  } catch (error) {
    return { data: null as T | null, error: toApiError(error) };
  }
}
