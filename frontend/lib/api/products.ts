import { apiRequest } from "@/lib/api/client";
import type {
  ProductDetailQuery,
  ProductDetailResponse,
  ProductListQuery,
  ProductListResponse
} from "@/lib/api/types";

export function getProducts(query: ProductListQuery = {}) {
  return apiRequest<ProductListResponse>("products", { query });
}

export function getProductDetail(productId: string | number, query: ProductDetailQuery = {}) {
  return apiRequest<ProductDetailResponse>(`products/${productId}`, { query });
}
