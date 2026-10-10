"""Potongan spesifikasi OpenAPI yang dipakai bersama oleh semua blueprint."""

SKEMA_KEAMANAN = {
    "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    "cookieAccess": {"type": "apiKey", "in": "cookie", "name": "access_token_cookie"},
    "cookieRefresh": {"type": "apiKey", "in": "cookie", "name": "refresh_token_cookie"},
}

# Endpoint terlindungi menerima token dari header (Flutter) atau cookie (web admin).
SEMUA_KANAL_ACCESS = [{"bearerAuth": []}, {"cookieAccess": []}]
SEMUA_KANAL_REFRESH = [{"bearerAuth": []}, {"cookieRefresh": []}]

KETERANGAN_ERROR = {
    400: "Format JSON tidak valid",
    401: "Belum masuk, token tidak valid, atau sesi berakhir",
    403: "Akses ditolak",
    422: "Data tidak valid",
    429: "Terlalu banyak percobaan",
}


def respons_problem_doc(*kode: int) -> dict[int, dict]:
    """Respons error untuk spesifikasi OpenAPI dengan Content-Type yang sebenarnya dikirim server."""
    return {
        k: {
            "description": KETERANGAN_ERROR[k],
            "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}},
        }
        for k in kode
    }


# flask-openapi3 otomatis menambahkan respons 422 berbentuk array; diganti supaya sesuai Problem Details.
RESPONS_422 = respons_problem_doc(422)
