import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "node:crypto";
import { unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { appConfig } from "@/lib/config";
import { proxyBackendRequest } from "@/lib/backend-proxy";

export const dynamic = "force-dynamic";

const ALLOWED_IMPORT_TYPES = new Set([
  "products",
  "sales",
  "inventory",
  "suppliers"
]);

function sanitizeFilename(filename: string) {
  const normalized = filename.replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  return normalized || "upload.csv";
}

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

  const contentType = request.headers.get("content-type") ?? "";
  if (contentType.includes("multipart/form-data")) {
    const formData = await request.formData();
    const file = formData.get("file");

    if (!(file instanceof File)) {
      return NextResponse.json(
        {
          error: {
            code: "invalid_import_file",
            message: "Attach a CSV file to import.",
            details: {}
          }
        },
        { status: 400 }
      );
    }

    const safeFilename = sanitizeFilename(file.name);
    const tempPath = join(tmpdir(), `chainwatch-${params.importType}-${randomUUID()}-${safeFilename}`);

    try {
      await writeFile(tempPath, Buffer.from(await file.arrayBuffer()));

      const response = await fetch(`${appConfig.apiBaseUrl}/imports/${params.importType}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ filePath: tempPath }),
        cache: "no-store"
      });

      return new NextResponse(response.body, {
        status: response.status,
        headers: {
          "content-type": response.headers.get("content-type") ?? "application/json",
          "cache-control": "no-store"
        }
      });
    } finally {
      await unlink(tempPath).catch(() => undefined);
    }
  }

  return proxyBackendRequest(request, `imports/${params.importType}`);
}
