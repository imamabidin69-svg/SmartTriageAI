export function getHomeRouteForRole(role: unknown): string {
  switch (role) {
    case "admin_faskes":
      return "/admin/staff";
    case "petugas_pendaftaran":
      return "/pasien";
    case "super_admin":
      return "/superadmin";
    case "auditor":
      return "/auditor";
    case "dinas_kesehatan":
      return "/dinas-kesehatan";
    default:
      return "/dashboard";
  }
}
