"""Lingkungan Alembic untuk Flask-Migrate.

Migrasi dijalankan dengan role pemilik skema (DATABASE_URL_MIGRASI), bukan role aplikasi,
karena role aplikasi sengaja tidak punya hak membuat tabel maupun mengubah log_audit.
"""

import logging
from logging.config import fileConfig

import sqlalchemy as sa
from alembic import context
from flask import current_app

config = context.config

# disable_existing_loggers=False supaya logger aplikasi tetap aktif setelah migrasi dijalankan.
fileConfig(config.config_file_name, disable_existing_loggers=False)
logger = logging.getLogger("alembic.env")


def url_migrasi() -> str:
    return current_app.config.get("SQLALCHEMY_MIGRASI_URI") or current_app.config["SQLALCHEMY_DATABASE_URI"]


config.set_main_option("sqlalchemy.url", url_migrasi().replace("%", "%%"))
target_db = current_app.extensions["migrate"].db


def get_metadata() -> sa.MetaData:
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=get_metadata(),
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Mencegah autogenerate membuat berkas migrasi kosong bila skema tidak berubah.
    def process_revision_directives(_context, _revision, directives):
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("Tidak ada perubahan skema.")

    conf_args = current_app.extensions["migrate"].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    engine = sa.create_engine(url_migrasi(), poolclass=sa.pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=get_metadata(), **conf_args)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
