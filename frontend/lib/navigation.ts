export type RouteKey =
  | "dashboard"
  | "map"
  | "products"
  | "reports"
  | "chat"
  | "settings";

export type ShellVariant = "standard" | "chat-mobile-focus";

export type NavigationItem = {
  key: RouteKey;
  href: string;
  label: string;
  description: string;
  icon: string;
  mobileVisible: boolean;
};

export type ResolvedRouteMeta = {
  key: RouteKey;
  href: string;
  activeHref: string;
  label: string;
  icon: string;
  shellVariant: ShellVariant;
  desktopTitle: string;
  desktopSearchPlaceholder?: string;
  desktopStatusLabel: string;
  desktopStatusTone: "success" | "caution" | "danger";
  productContext?: string;
};

export const NAV_ITEMS: readonly NavigationItem[] = [
  {
    key: "dashboard",
    href: "/",
    label: "Dashboard",
    description: "Operational summary, KPIs, alerts, and trends.",
    icon: "dashboard",
    mobileVisible: true
  },
  {
    key: "map",
    href: "/map",
    label: "Map",
    description: "Country-level external risk view and exposure drilldown.",
    icon: "map",
    mobileVisible: true
  },
  {
    key: "products",
    href: "/products/1",
    label: "Products",
    description: "Single-SKU demand, inventory, fulfillment, and supplier view.",
    icon: "inventory_2",
    mobileVisible: false
  },
  {
    key: "reports",
    href: "/reports",
    label: "Reports",
    description: "Generated artifacts, scope filters, and report previews.",
    icon: "assessment",
    mobileVisible: false
  },
  {
    key: "chat",
    href: "/chat",
    label: "Chat",
    description: "Grounded questions with citations and agent traces.",
    icon: "chat",
    mobileVisible: true
  },
  {
    key: "settings",
    href: "/settings",
    label: "Settings",
    description: "Runtime health, import history, and provider readiness.",
    icon: "settings",
    mobileVisible: true
  }
] as const;

function findItem(key: RouteKey) {
  return NAV_ITEMS.find((item) => item.key === key)!;
}

export function getRouteMeta(pathname: string): ResolvedRouteMeta {
  if (pathname.startsWith("/map")) {
    const item = findItem("map");
    return {
      ...item,
      activeHref: item.href,
      shellVariant: "standard",
      desktopTitle: "Global Risk Map",
      desktopSearchPlaceholder: "SEARCH COUNTRIES OR SUPPLIERS...",
      desktopStatusLabel: "System Live",
      desktopStatusTone: "success"
    };
  }

  if (pathname.startsWith("/reports")) {
    const item = findItem("reports");
    return {
      ...item,
      activeHref: item.href,
      shellVariant: "standard",
      desktopTitle: "Reports & Analysis",
      desktopSearchPlaceholder: "Search archived reports...",
      desktopStatusLabel: "Live Status",
      desktopStatusTone: "caution"
    };
  }

  if (pathname.startsWith("/chat")) {
    const item = findItem("chat");
    return {
      ...item,
      activeHref: item.href,
      shellVariant: "chat-mobile-focus",
      desktopTitle: "Intelligence Assistant",
      desktopStatusLabel: "Heartbeat Stable",
      desktopStatusTone: "success"
    };
  }

  if (pathname.startsWith("/settings")) {
    const item = findItem("settings");
    return {
      ...item,
      activeHref: item.href,
      shellVariant: "standard",
      desktopTitle: "System Settings",
      desktopStatusLabel: "System Live",
      desktopStatusTone: "success"
    };
  }

  if (pathname.startsWith("/products/")) {
    const item = findItem("products");
    const context = pathname.split("/").filter(Boolean).at(-1) || "1";

    return {
      ...item,
      activeHref: item.href,
      shellVariant: "standard",
      desktopTitle: "Product Intelligence",
      desktopSearchPlaceholder: "Search logistics nodes...",
      desktopStatusLabel: "Heartbeat Connected",
      desktopStatusTone: "success",
      productContext: context
    };
  }

  const item = findItem("dashboard");
  return {
    ...item,
    activeHref: item.href,
    shellVariant: "standard",
    desktopTitle: "Dashboard",
    desktopSearchPlaceholder: "Search SKU, Supplier, or Region...",
    desktopStatusLabel: "System Status",
    desktopStatusTone: "success"
  };
}
