export const COUNTRY_NAME_BY_CODE: Record<string, string> = {
  AE: "United Arab Emirates",
  BR: "Brazil",
  CA: "Canada",
  CN: "China",
  DE: "Germany",
  FR: "France",
  GB: "United Kingdom",
  IN: "India",
  IR: "Iran",
  JP: "Japan",
  KR: "South Korea",
  MX: "Mexico",
  OM: "Oman",
  SA: "Saudi Arabia",
  SG: "Singapore",
  US: "United States",
  VN: "Vietnam"
};

export const COUNTRY_NUMERIC_BY_CODE: Record<string, string> = {
  AE: "784",
  BR: "076",
  CA: "124",
  CN: "156",
  DE: "276",
  FR: "250",
  GB: "826",
  IN: "356",
  IR: "364",
  JP: "392",
  KR: "410",
  MX: "484",
  OM: "512",
  SA: "682",
  US: "840",
  VN: "704"
};

export function countryNameFromCode(countryCode: string) {
  return COUNTRY_NAME_BY_CODE[countryCode] ?? countryCode;
}

export function countryNumericCode(countryCode: string) {
  return COUNTRY_NUMERIC_BY_CODE[countryCode];
}
