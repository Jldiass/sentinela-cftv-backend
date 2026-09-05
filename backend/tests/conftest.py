import os

import pytest

# As configurações precisam existir antes de qualquer módulo da aplicação ser
# importado durante a coleta do pytest.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("PUBLIC_RTMP_BASE_URL", "rtmp://localhost:1935")
os.environ.setdefault("PUBLIC_HLS_BASE_URL", "http://localhost:8888")
os.environ.setdefault("PUBLIC_PLAYBACK_BASE_URL", "http://localhost:9996")
os.environ.setdefault("RECORD_DELETE_AFTER", "1h")
os.environ.setdefault("AUTH_JWT_SECRET", "unit-test-secret-with-at-least-32-characters")
os.environ.setdefault("AUTH_DEBUG_RETURN_RESET_TOKEN", "true")

from app.database import Base, SessionLocal, engine
from app.services.rbac import ensure_rbac_catalog


@pytest.fixture(autouse=True)
def clean_database():
    """Isola cada teste e mantém o catálogo RBAC disponível."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_rbac_catalog(db)
    yield
    Base.metadata.drop_all(engine)
