"""SQLite 连接与会话工厂。"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def resolve_db_path() -> Path:
    """优先使用环境变量，便于 Docker Volume 挂载到 /data。"""
    raw = os.getenv("DATABASE_PATH")
    if raw:
        return Path(raw)
    # 本地开发默认落到仓库根目录 data/rally.db
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "data" / "rally.db"


DB_PATH = resolve_db_path()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
