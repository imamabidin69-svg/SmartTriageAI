"""Blueprint rekap: rekap evaluasi dengan ekspor CSV dan pembacaan log audit, khusus admin (FR-09)."""

from flask import Response, jsonify, stream_with_context
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.middleware.auth import role_required
from app.models.enums import Peran
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.log_audit_service import LogAuditService
from app.services.rekap_service import PenulisCsv, RekapService, rentang_tanggal
from app.utils.schemas import (
    ItemLogAudit,
    LogAuditQuery,
    LogAuditResponse,
    PenggunaRingkas,
    RekapQuery,
    RekapResponse,
)

rekap_bp = APIBlueprint(
    "rekap",
    __name__,
    abp_tags=[Tag(name="Rekap")],
    abp_security=SEMUA_KANAL_ACCESS,
    abp_responses=RESPONS_422,
)


@rekap_bp.get(
    "/rekap",
    summary="Rekap evaluasi triase",
    description=(
        "Jumlah triase per level, rata-rata waktu tunggu, persentase koreksi dokter, jumlah triase ulang, dan "
        "akurasi pemindaian dalam rentang tanggal WIB (bawaan 7 hari terakhir, maksimal 366 hari). format=csv "
        "mengirim berkas CSV berpemisah titik koma berisi agregat saja, tanpa data pasien."
    ),
    # Bila format=csv, respons 200 berupa berkas text/csv; skema di bawah untuk format JSON.
    responses={200: RekapResponse, **respons_problem_doc(401, 403)},
)
@role_required(Peran.ADMIN)
@validate_request()
def rekap(query: RekapQuery):
    dari, sampai = rentang_tanggal(query.dari, query.sampai)
    hasil = RekapService().hitung(dari, sampai)
    if query.format == "csv":
        nama = f"rekap-{dari.isoformat()}_{sampai.isoformat()}.csv"
        return Response(
            stream_with_context(PenulisCsv().stream(hasil)),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{nama}"'},
        )
    respons = RekapResponse(**{f: getattr(hasil, f) for f in RekapResponse.model_fields})
    return jsonify(respons.model_dump(mode="json"))


@rekap_bp.get(
    "/admin/log-audit",
    summary="Log audit",
    description=(
        "Jejak validasi, koreksi, review, perubahan konfigurasi, dan kelola staf, terbaru lebih dulu. "
        "Halaman berikutnya diambil dengan mengirim kursor_berikutnya sebagai parameter kursor."
    ),
    responses={200: LogAuditResponse, **respons_problem_doc(401, 403)},
)
@role_required(Peran.ADMIN)
@validate_request()
def log_audit(query: LogAuditQuery):
    halaman = LogAuditService().ambil(query)
    items = [
        ItemLogAudit(
            id_log=log.id_log,
            waktu=log.waktu,
            aksi=log.aksi,
            aktor=PenggunaRingkas.model_validate(log.aktor),
            id_triase=log.id_triase,
            level_sebelum=log.level_sebelum,
            level_sesudah=log.level_sesudah,
            catatan=log.catatan,
        )
        for log in halaman.items
    ]
    return jsonify(LogAuditResponse(items=items, kursor_berikutnya=halaman.kursor_berikutnya).model_dump(mode="json"))
