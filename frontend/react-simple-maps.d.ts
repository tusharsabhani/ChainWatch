declare module "react-simple-maps" {
  import type { ComponentType, ReactNode } from "react";

  export const ComposableMap: ComponentType<Record<string, unknown>>;
  export const Geography: ComponentType<Record<string, unknown>>;
  export const Marker: ComponentType<Record<string, unknown>>;
  export const ZoomableGroup: ComponentType<Record<string, unknown>>;
  export const Sphere: ComponentType<Record<string, unknown>>;
  export const Graticule: ComponentType<Record<string, unknown>>;
  export const Annotation: ComponentType<Record<string, unknown>>;

  export const Geographies: ComponentType<{
    geography: unknown;
    children: (args: {
      geographies: Array<Record<string, unknown>>;
      outline?: unknown;
      borders?: unknown;
    }) => ReactNode;
  }>;
}
