"""Fungsi bantu untuk tes autentikasi."""

from flask.testing import FlaskClient

PASSWORD_TES = "PasswordTes123"


def login_web(client: FlaskClient, email: str, password: str = PASSWORD_TES):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def login_mobile(client: FlaskClient, email: str, password: str = PASSWORD_TES):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}, headers={"X-Client": "mobile"}
    )


def nilai_cookie(client: FlaskClient, nama: str, path: str = "/") -> str | None:
    cookie = client.get_cookie(nama, path=path)
    return cookie.value if cookie else None


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def header_masuk(client: FlaskClient, email: str) -> dict[str, str]:
    """Header Authorization untuk pengguna yang sudah dibuat, lewat login mobile."""
    return bearer(login_mobile(client, email).get_json()["access_token"])
