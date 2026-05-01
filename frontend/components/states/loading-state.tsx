export function LoadingState({
  title = "Loading",
  description = "Fetching the next view."
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="rounded-xl border border-outline-variant bg-white p-6">
      <div className="space-y-3">
        <div className="h-3 w-24 animate-pulse rounded-full bg-slate-200" />
        <div className="h-7 w-56 animate-pulse rounded-full bg-slate-200" />
        <div className="h-4 w-full max-w-2xl animate-pulse rounded-full bg-slate-200" />
        <div className="grid gap-3 pt-4 sm:grid-cols-3">
          <div className="h-28 animate-pulse rounded-xl bg-slate-100" />
          <div className="h-28 animate-pulse rounded-xl bg-slate-100" />
          <div className="h-28 animate-pulse rounded-xl bg-slate-100" />
        </div>
        <div className="pt-3">
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="mt-1 text-sm text-slate-600">{description}</p>
        </div>
      </div>
    </div>
  );
}
