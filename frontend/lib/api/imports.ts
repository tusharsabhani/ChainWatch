import { apiRequest } from "@/lib/api/client";
import type { ImportStartRequest, ImportStartResponse, ImportsListResponse } from "@/lib/api/types";

export function getImports() {
  return apiRequest<ImportsListResponse>("imports");
}

export function startProductsImport(payload: ImportStartRequest) {
  return apiRequest<ImportStartResponse>("imports/products", {
    method: "POST",
    body: payload
  });
}

export function startSalesImport(payload: ImportStartRequest) {
  return apiRequest<ImportStartResponse>("imports/sales", {
    method: "POST",
    body: payload
  });
}

export function startInventoryImport(payload: ImportStartRequest) {
  return apiRequest<ImportStartResponse>("imports/inventory", {
    method: "POST",
    body: payload
  });
}

export function startSuppliersImport(payload: ImportStartRequest) {
  return apiRequest<ImportStartResponse>("imports/suppliers", {
    method: "POST",
    body: payload
  });
}
