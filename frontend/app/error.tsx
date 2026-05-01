"use client";

import { ErrorState } from "@/components/states/error-state";

export default function GlobalError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="bg-background p-6 text-on-background">
        <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-3xl items-center">
          <ErrorState
            title="The app shell hit an unexpected error"
            message={error.message || "Something went wrong while rendering the page."}
            retryLabel="Reset app"
            onRetry={reset}
          />
        </div>
      </body>
    </html>
  );
}
