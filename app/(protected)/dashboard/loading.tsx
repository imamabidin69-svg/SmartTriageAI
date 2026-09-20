/**
 * loading.tsx - Streaming Skeleton Fallback UI (Modul 6, Bab E). Next.js
 * otomatis menampilkan ini saat navigasi menuju /dashboard, selagi Server
 * Component page.tsx pada segmen ini masih menyiapkan data (mis. saat
 * baru datang dari halaman login).
 */
export default function DashboardLoading() {
  return (
    <div className="animate-pulse space-y-6" aria-hidden="true">
      <div className="h-8 bg-slate-200 dark:bg-slate-900 rounded w-1/3" />
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-[68px] bg-slate-200 dark:bg-slate-900 rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-36 bg-slate-200 dark:bg-slate-900 rounded-xl" />
        ))}
      </div>
    </div>
  );
}
