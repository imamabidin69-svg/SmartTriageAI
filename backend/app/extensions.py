"""Objek ekstensi Flask yang dibuat sekali di level modul lalu dipasang di create_app."""

from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Nama constraint dibuat tetap supaya migrasi Alembic stabil. Constraint CHECK dan index
# selalu diberi nama lengkap secara eksplisit di model (misalnya ck_saturasi dari Desain Bab 5).
KONVENSI_NAMA = {
    "ix": "%(column_0_label)s_idx",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class ModelDasar(DeclarativeBase):
    metadata = MetaData(naming_convention=KONVENSI_NAMA)


db = SQLAlchemy(model_class=ModelDasar)
migrate = Migrate()
jwt = JWTManager()
# Limiter wajib disimpan di level modul: Flask-Limiter hanya menyimpan weak reference ke dirinya.
limiter = Limiter(key_func=get_remote_address)
