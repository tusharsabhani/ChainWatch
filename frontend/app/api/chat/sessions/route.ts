import { NextRequest } from "next/server";

import { proxyBackendRequest } from "@/lib/backend-proxy";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  return proxyBackendRequest(request, "chat/sessions");
}

export async function POST(request: NextRequest) {
  return proxyBackendRequest(request, "chat/sessions");
}
