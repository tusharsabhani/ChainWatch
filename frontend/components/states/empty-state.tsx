export function EmptyState({
  title,
  description
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-outline-variant bg-surface-container-low p-6">
      <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        Empty state
      </p>
      <h3 className="mt-3 font-display text-xl font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{description}</p>
    </div>
  );
}
