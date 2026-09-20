export default function TriaseDetailLoading() {
  return (
    <div className="max-w-3xl animate-pulse space-y-4" aria-hidden="true">
      <div className="h-4 bg-slate-200 dark:bg-slate-900 rounded w-40" />
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 space-y-4">
        <div className="h-6 bg-slate-200 dark:bg-slate-900 rounded w-1/2" />
        <div className="h-24 bg-slate-200 dark:bg-slate-900 rounded" />
        <div className="h-24 bg-slate-200 dark:bg-slate-900 rounded" />
      </div>
    </div>
  );
}
