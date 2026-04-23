export function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="text-slate-600 text-sm">Coming in a later sprint.</p>
    </div>
  );
}
