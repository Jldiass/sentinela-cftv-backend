"""Baseline compatível e fundação de RBAC, mosaicos e conectividade.

Revision ID: 0001_secure_mosaics_rbac
Revises:
Create Date: 2026-09-04
"""

from alembic import op

from app import models  # noqa: F401
from app.database import Base

revision = "0001_secure_mosaics_rbac"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Compatível com o SQLite já existente no Railway: cria somente tabelas e
    # índices ausentes, preservando câmeras, usuários, eventos e gravações.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    # O baseline não remove dados automaticamente. Downgrades destrutivos devem
    # ser feitos por uma migração específica, com backup validado.
    pass
