import { NextRequest } from "next/server";

import { proxyBackendRequest } from "@/lib/backend-proxy";

export const dynamic = "force-dynamic";

export async function GET(
  request: NextRequest,
  { params }: { params: { reportId: string } }
) {
  return proxyBackendRequest(request, `reports/${params.reportId}`);
}
