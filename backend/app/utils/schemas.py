"""Model Pydantic untuk request dan response API."""

import uuid
from typing import Annotated, Literal

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints
from pydantic_core import PydanticCustomError

from app.models.enums import Peran

PANJANG_MAKS_EMAIL = 150


def normalisasi_email(nilai: str) -> str:
    """Memvalidasi email lalu mengubahnya ke bentuk baku (tanpa spasi, huruf kecil).

    Fungsi yang sama dipakai untuk pencarian akun dan kunci pembatas login, supaya variasi
    spasi atau huruf besar tidak dianggap sebagai email yang berbeda.
    """
    try:
        hasil = validate_email(nilai.strip(), check_deliverability=False)
    except EmailNotValidError as galat:
        raise PydanticCustomError("kustom_email", "Format email tidak valid.") from galat
    return hasil.normalized.lower()


Email = Annotated[str, StringConstraints(max_length=PANJANG_MAKS_EMAIL), AfterValidator(normalisasi_email)]


class SkemaDasar(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(SkemaDasar):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class LoginHeader(BaseModel):
    """Aplikasi Flutter mengirim X-Client: mobile supaya token dikirim di body, bukan cookie."""

    model_config = ConfigDict(populate_by_name=True)

    x_client: Literal["web", "mobile"] = Field(
        "web",
        alias="X-Client",
        description="Jenis klien. Tanpa header ini klien dianggap web dan token disimpan di cookie HttpOnly.",
    )


class PenggunaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pengguna: uuid.UUID
    nama: str
    email: str
    peran: Peran
    is_active: bool


class SesiResponse(BaseModel):
    """Respons login dan refresh. Token hanya diisi untuk klien mobile."""

    pengguna: PenggunaResponse
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: Literal["Bearer"] | None = None
    expires_in: int | None = Field(None, description="Umur access token dalam detik.")


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "gagal"]
    komponen: dict[str, Literal["ok", "gagal"]]
