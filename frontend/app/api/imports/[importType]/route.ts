import { NextRequest, NextResponse } from "next/server";

import { proxyBackendRequest } from "@/lib/backend-proxy";

export const dynamic = "force-dynamic";

const ALLOWED_IMPORT_TYPES = new Set([
  "products",
  "sales",
  "inventory",
  "suppliers"
]);

export async function POST(
  request: NextRequest,
  { params }: { params: { importType: string } }
) {
  if (!ALLOWED_IMPORT_TYPES.has(params.importType)) {
    return NextResponse.json(
      {
        error: {
          code: "unsupported_import_type",
          message: `Import type ${params.importType} is not supported.`,
          details: {}
        }
      },
      { status: 404 }
    );
  }

  return proxyBackendRequest(request, `imports/${params.importType}`);
}
