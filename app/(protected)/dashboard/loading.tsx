export default function DashboardLoading() {
  return (
    <div className="motion-safe:animate-pulse space-y-6" aria-hidden="true">
      <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded-lg w-1/3" />
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={`h-[68px] bg-slate-200 dark:bg-slate-800 rounded-xl ${i === 1 ? "col-span-2 md:col-span-1" : ""}`}
          />
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-36 bg-slate-200 dark:bg-slate-800 rounded-xl" />
        ))}
      </div>
    </div>
  );
}
