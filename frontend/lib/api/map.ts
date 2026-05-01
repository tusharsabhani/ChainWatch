import { apiRequest } from "@/lib/api/client";
import type {
  CountryDetailResponse,
  MapCountriesQuery,
  MapCountriesResponse
} from "@/lib/api/types";

export function getMapCountries(query: MapCountriesQuery = {}) {
  return apiRequest<MapCountriesResponse>("map/countries", { query });
}

export function getCountryDetail(countryCode: string) {
  return apiRequest<CountryDetailResponse>(`map/countries/${countryCode}`);
}
