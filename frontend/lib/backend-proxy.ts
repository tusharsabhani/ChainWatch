import { NextRequest, NextResponse } from "next/server";

import { appConfig } from "@/lib/config";

function buildBackendUrl(request: NextRequest, backendPath: string) {
  const url = new URL(backendPath, `${appConfig.apiBaseUrl}/`);

  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value);
  });

  return url;
}

export async function proxyBackendRequest(
  request: NextRequest,
  backendPath: string
) {
  const url = buildBackendUrl(request, backendPath);
  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.text();
  const contentType = request.headers.get("content-type");

  const response = await fetch(url, {
    method: request.method,
    headers: contentType ? { "Content-Type": contentType } : undefined,
    body,
    cache: "no-store"
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store"
    }
  });
}
