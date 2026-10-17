"""Kelola akun staf oleh admin dan ganti password sendiri (FR-01, Desain 2.1, keputusan K7, K18, D1-D6)."""

import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Pengguna
from app.models.enums import AksiAudit, Peran
from app.services.audit_logger import AuditLogger
from app.utils.errors import KonflikError, TidakDitemukanError, ValidasiGagalError
from app.utils.pembatas import PembatasPerAkun
from app.utils.schemas import StafPatch, StafRequest

# Tanpa karakter yang mudah tertukar saat dibacakan atau diketik ulang: 0/O/o, 1/l/I.
HURUF_PASSWORD = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"  # noqa: S105 (abjad, bukan password)
PANJANG_PASSWORD_SEMENTARA = 12
FIELD_DATA = ("nama", "email", "peran")


def buat_password_sementara() -> str:
    return "".join(secrets.choice(HURUF_PASSWORD) for _ in range(PANJANG_PASSWORD_SEMENTARA))


def _identitas(staf: Pengguna) -> str:
    return f"id_pengguna={staf.id_pengguna}; email={staf.email}"


class StafService:
    def daftar(self, peran: Peran | None = None, aktif: bool | None = None) -> list[Pengguna]:
        kueri = select(Pengguna).order_by(Pengguna.nama, Pengguna.id_pengguna)
        if peran is not None:
            kueri = kueri.where(Pengguna.peran == peran)
        if aktif is not None:
            kueri = kueri.where(Pengguna.is_active == aktif)
        return list(db.session.scalars(kueri))

    def tambah(self, data: StafRequest, admin: Pengguna) -> tuple[Pengguna, str]:
        password = buat_password_sementara()
        try:
            self._email_belum_dipakai(data.email)
            staf = Pengguna(nama=data.nama, email=data.email, peran=data.peran)
            staf.atur_password(password)
            db.session.add(staf)
            db.session.flush()
            AuditLogger().catat(AksiAudit.TAMBAH_STAF, admin, catatan=f"{_identitas(staf)}; peran={staf.peran.value}")
            db.session.commit()
        except IntegrityError as galat:
            db.session.rollback()
            raise KonflikError("Email ini sudah dipakai akun lain.") from galat
        except Exception:
            db.session.rollback()
            raise
        return staf, password

    def ubah(self, id_pengguna: uuid.UUID, data: StafPatch, admin: Pengguna) -> tuple[Pengguna, str | None]:
        try:
            hasil = self._ubah(id_pengguna, data, admin)
            db.session.commit()
        except IntegrityError as galat:
            db.session.rollback()
            raise KonflikError("Email ini sudah dipakai akun lain.") from galat
        except Exception:
            db.session.rollback()
            raise
        return hasil

    def _ubah(self, id_pengguna: uuid.UUID, data: StafPatch, admin: Pengguna) -> tuple[Pengguna, str | None]:
        # Bila perubahan bisa mengurangi jumlah admin aktif, semua admin aktif dikunci lebih dulu dalam urutan
        # tetap. Dua admin yang saling menonaktifkan pada saat bersamaan lalu antre, bukan saling menunggu.
        admin_aktif = None
        if "peran" in data.model_fields_set or data.is_active is False:
            admin_aktif = db.session.scalars(
                select(Pengguna.id_pengguna)
                .where(Pengguna.peran == Peran.ADMIN, Pengguna.is_active.is_(True))
                .order_by(Pengguna.id_pengguna)
                .with_for_update()
            ).all()
        staf = db.session.scalar(
            select(Pengguna)
            .where(Pengguna.id_pengguna == id_pengguna)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if staf is None:
            raise TidakDitemukanError("Staf tidak ditemukan.")

        dikirim = data.model_fields_set
        diubah = {f: getattr(data, f) for f in FIELD_DATA if f in dikirim and getattr(data, f) != getattr(staf, f)}
        aktif_baru = data.is_active if "is_active" in dikirim and data.is_active != staf.is_active else None
        self._jaga_admin(staf, admin, diubah.get("peran"), aktif_baru, admin_aktif or [])
        if "email" in diubah:
            self._email_belum_dipakai(diubah["email"])

        audit = AuditLogger()
        if diubah:
            catatan = "; ".join(f"{f}: {self._teks(getattr(staf, f))} -> {self._teks(v)}" for f, v in diubah.items())
            audit.catat(AksiAudit.UBAH_STAF, admin, catatan=f"{_identitas(staf)}; {catatan}")
            for field, nilai in diubah.items():
                setattr(staf, field, nilai)
        if aktif_baru is not None:
            staf.is_active = aktif_baru
            aksi = AksiAudit.AKTIFKAN_STAF if aktif_baru else AksiAudit.NONAKTIFKAN_STAF
            audit.catat(aksi, admin, catatan=_identitas(staf))

        password = None
        if data.atur_ulang_password:
            password = buat_password_sementara()
            staf.atur_password(password)
            # Password tidak pernah ditulis ke log audit maupun log aplikasi.
            audit.catat(AksiAudit.ATUR_ULANG_PASSWORD, admin, catatan=_identitas(staf))
        db.session.flush()
        return staf, password

    @staticmethod
    def _teks(nilai: object) -> str:
        return nilai.value if isinstance(nilai, Peran) else str(nilai)

    @staticmethod
    def _email_belum_dipakai(email: str) -> None:
        if db.session.scalar(select(Pengguna.id_pengguna).where(Pengguna.email == email)) is not None:
            raise KonflikError("Email ini sudah dipakai akun lain.")

    @staticmethod
    def _jaga_admin(
        staf: Pengguna,
        admin: Pengguna,
        peran_baru: Peran | None,
        aktif_baru: bool | None,
        admin_aktif: list[uuid.UUID],
    ) -> None:
        """Keputusan K18: admin tidak mengunci dirinya sendiri dan sistem tidak kehabisan admin aktif."""
        turun_peran = peran_baru is not None and staf.peran == Peran.ADMIN
        dinonaktifkan = aktif_baru is False
        if not (turun_peran or dinonaktifkan):
            return
        if staf.id_pengguna == admin.id_pengguna:
            if dinonaktifkan:
                raise KonflikError("Anda tidak bisa menonaktifkan akun Anda sendiri.")
            raise KonflikError("Anda tidak bisa mengubah peran akun Anda sendiri.")
        if staf.peran == Peran.ADMIN and staf.is_active and not [i for i in admin_aktif if i != staf.id_pengguna]:
            raise KonflikError("Harus ada minimal satu admin aktif.")

    def ganti_password(self, pengguna: Pengguna, password_lama: str, password_baru: str) -> None:
        pembatas = PembatasPerAkun(
            "BATAS_GANTI_PASSWORD",
            "ganti-password",
            pengguna,
            "Terlalu banyak percobaan dengan password lama yang salah. Coba lagi beberapa saat lagi.",
        )
        pembatas.periksa()
        if not pengguna.cek_password(password_lama):
            pembatas.catat_gagal()
            raise ValidasiGagalError([{"field": "password_lama", "pesan": "Password lama tidak cocok."}])
        try:
            pengguna.atur_password(password_baru)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
