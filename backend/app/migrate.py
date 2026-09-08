"""SQLite 轻量迁移：老库加字段、换唯一约束、职责字典对齐。"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .database import Base

SCHEMA_VERSION = "3"

DUTY_BY_KEY = {"tank": "Tank", "dps": "DPS", "support": "Support"}


def migrate_schema(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_meta ("
                "k VARCHAR(32) PRIMARY KEY, v VARCHAR(32) NOT NULL)"
            )
        )
        current = conn.execute(
            text("SELECT v FROM schema_meta WHERE k = 'version'")
        ).scalar()
        _ensure_duty_column(conn)
        _ensure_profession_columns(conn)
        _align_roles(conn)
        _rebuild_checkin_unique(conn)
        _backfill_duty(conn)
        if current != SCHEMA_VERSION:
            conn.execute(text("DELETE FROM schema_meta WHERE k = 'version'"))
            conn.execute(
                text("INSERT INTO schema_meta (k, v) VALUES ('version', :v)"),
                {"v": SCHEMA_VERSION},
            )


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name},
    ).first()
    return row is not None


def _columns(conn, table: str) -> set[str]:
    return {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}


def _ensure_duty_column(conn) -> None:
    if not _table_exists(conn, "checkins"):
        return
    if "duty" not in _columns(conn, "checkins"):
        # 显式 VARCHAR 职责：Tank / DPS / Support，与 role_id 同步写入
        conn.execute(text("ALTER TABLE checkins ADD COLUMN duty VARCHAR(16)"))


def _ensure_profession_columns(conn) -> None:
    """旧库补齐甲种 / 职业族 / 特化类型，便于核心+精英特化一起展示。"""
    if not _table_exists(conn, "professions"):
        return
    cols = _columns(conn, "professions")
    if "armor" not in cols:
        conn.execute(text("ALTER TABLE professions ADD COLUMN armor VARCHAR(16) DEFAULT 'heavy'"))
    if "family_key" not in cols:
        conn.execute(text("ALTER TABLE professions ADD COLUMN family_key VARCHAR(32) DEFAULT ''"))
    if "spec_kind" not in cols:
        conn.execute(text("ALTER TABLE professions ADD COLUMN spec_kind VARCHAR(16) DEFAULT 'core'"))
    conn.execute(
        text(
            "UPDATE professions SET family_key = key "
            "WHERE family_key IS NULL OR family_key = ''"
        )
    )


def _align_roles(conn) -> None:
    """heal 并入 support，补齐 tank。"""
    if not _table_exists(conn, "roles"):
        return
    rows = {r[0]: r[1] for r in conn.execute(text("SELECT key, id FROM roles"))}
    if "tank" not in rows:
        conn.execute(
            text(
                "INSERT INTO roles (key, name_zh, name_en, color, sort_order) "
                "VALUES ('tank', '坦', 'Tank', '#C45C5C', 1)"
            )
        )
        rows = {r[0]: r[1] for r in conn.execute(text("SELECT key, id FROM roles"))}

    conn.execute(text("UPDATE roles SET name_zh='坦', name_en='Tank', color='#C45C5C', sort_order=1 WHERE key='tank'"))
    conn.execute(text("UPDATE roles SET name_zh='DPS', name_en='DPS', color='#E8A317', sort_order=2 WHERE key='dps'"))
    conn.execute(text("UPDATE roles SET name_zh='辅助', name_en='Support', color='#7EC8E3', sort_order=3 WHERE key='support'"))

    if "heal" in rows and "support" in rows:
        heal_id, support_id = rows["heal"], rows["support"]
        if _table_exists(conn, "checkins"):
            conn.execute(
                text("UPDATE checkins SET role_id=:sid WHERE role_id=:hid"),
                {"sid": support_id, "hid": heal_id},
            )
        conn.execute(text("DELETE FROM roles WHERE key='heal'"))


def _index_names(conn, table: str) -> set[str]:
    return {row[1] for row in conn.execute(text(f"PRAGMA index_list({table})"))}


def _rebuild_checkin_unique(conn) -> None:
    """同一人同一天可打多个职业+职责；仅相同组合去重。"""
    if not _table_exists(conn, "checkins"):
        return
    names = _index_names(conn, "checkins")
    if "uq_checkin_nick_date_prof_role" in names and "uq_checkin_nick_date" not in names:
        return

    cols = _columns(conn, "checkins")
    duty_select = "duty" if "duty" in cols else "NULL"
    conn.execute(
        text(
            """
            CREATE TABLE checkins_v2 (
                id INTEGER PRIMARY KEY,
                rally_date DATE NOT NULL,
                nickname VARCHAR(32) NOT NULL,
                profession_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                duty VARCHAR(16),
                created_at DATETIME,
                updated_at DATETIME,
                CONSTRAINT uq_checkin_nick_date_prof_role
                    UNIQUE (nickname, rally_date, profession_id, role_id),
                FOREIGN KEY(profession_id) REFERENCES professions(id),
                FOREIGN KEY(role_id) REFERENCES roles(id)
            )
            """
        )
    )
    conn.execute(
        text(
            f"""
            INSERT INTO checkins_v2
                (id, rally_date, nickname, profession_id, role_id, duty, created_at, updated_at)
            SELECT id, rally_date, nickname, profession_id, role_id, {duty_select}, created_at, updated_at
            FROM checkins
            """
        )
    )
    conn.execute(text("DROP TABLE checkins"))
    conn.execute(text("ALTER TABLE checkins_v2 RENAME TO checkins"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_checkins_rally_date ON checkins (rally_date)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_checkins_nickname ON checkins (nickname)"))


def _backfill_duty(conn) -> None:
    if not _table_exists(conn, "checkins") or "duty" not in _columns(conn, "checkins"):
        return
    mapping = {"tank": "Tank", "dps": "DPS", "support": "Support"}
    for key, duty in mapping.items():
        conn.execute(
            text(
                "UPDATE checkins SET duty=:duty WHERE role_id IN "
                "(SELECT id FROM roles WHERE key=:key) AND (duty IS NULL OR duty='')"
            ),
            {"duty": duty, "key": key},
        )
