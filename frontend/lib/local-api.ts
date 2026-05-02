"use client";

import { ApiError } from "@/lib/api/client";
import type { ErrorResponse } from "@/lib/api/types";

type QueryValue = string | number | boolean | null | undefined;
type LocalBody = FormData | BodyInit | Record<string, unknown> | unknown[];

type LocalApiOptions = Omit<RequestInit, "body"> & {
  query?: Record<string, QueryValue>;
  body?: LocalBody;
};

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const url = new URL(`/api/${path}`, window.location.origin);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === null || value === undefined || value === "") {
        continue;
      }

      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

export async function localApiRequest<T>(path: string, options: LocalApiOptions = {}) {
  const { query, body, headers, ...init } = options;
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  const hasRawBody =
    typeof body === "string" ||
    body instanceof Blob ||
    body instanceof ArrayBuffer ||
    ArrayBuffer.isView(body) ||
    body instanceof URLSearchParams;
  const response = await fetch(buildUrl(path, query), {
    ...init,
    cache: init.cache ?? "no-store",
    headers: {
      ...(body && !isFormData && !hasRawBody ? { "Content-Type": "application/json" } : {}),
      ...headers
    },
    body:
      body == null
        ? undefined
        : isFormData || hasRawBody
          ? body
          : JSON.stringify(body)
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

export async function safeLocalApiCall<T>(operation: () => Promise<T>) {
  try {
    const data = await operation();
    return { data, error: null as ApiError | null };
  } catch (error) {
    return {
      data: null as T | null,
      error:
        error instanceof ApiError ? error : new ApiError(error instanceof Error ? error.message : "Unexpected API error")
    };
  }
}
