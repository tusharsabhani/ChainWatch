import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { getHealth } from "@/lib/api";
import { safeApiCall } from "@/lib/api/client";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "ChainWatch",
    template: "%s | ChainWatch"
  },
  description:
    "Local-first retail risk intelligence for inventory pressure, supplier exposure, and fulfillment health."
};

export default async function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  const healthResult = await safeApiCall(() => getHealth());
  const healthCheckedAt = new Date().toISOString();

  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Work+Sans:wght@500;600&family=Material+Symbols+Outlined:wght@400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <AppShell initialHealth={healthResult.data} healthCheckedAt={healthCheckedAt}>
          {children}
        </AppShell>
      </body>
    </html>
  );
}
