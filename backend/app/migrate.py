"""SQLite 轻量迁移：老库加字段、换唯一约束、职责字典对齐。"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from . import models as _models  # noqa: F401  register tables on Base
from .database import Base

SCHEMA_VERSION = "5"
LEGACY_GUILD_NAME = "原有数据"

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
        _ensure_guild_tables(conn)
        _ensure_owner_columns(conn)
        _ensure_guild_id_columns(conn)
        _backfill_legacy_guild(conn)
        _finish_stale_rebuilds(conn)
        _rebuild_checkin_unique(conn)
        _rebuild_weekly_unique(conn)
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
                "VALUES ('tank', '坦', 'Tank', '#C45C5C', 3)"
            )
        )
        rows = {r[0]: r[1] for r in conn.execute(text("SELECT key, id FROM roles"))}

    conn.execute(text("UPDATE roles SET name_zh='输出', name_en='DPS', color='#E8A317', sort_order=1 WHERE key='dps'"))
    conn.execute(text("UPDATE roles SET name_zh='辅助', name_en='Support', color='#7EC8E3', sort_order=2 WHERE key='support'"))
    conn.execute(text("UPDATE roles SET name_zh='坦', name_en='Tank', color='#C45C5C', sort_order=3 WHERE key='tank'"))

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


def _ensure_guild_tables(conn) -> None:
    conn.execute(
        text(
            "CREATE TABLE IF NOT EXISTS guilds ("
            "id INTEGER PRIMARY KEY, "
            "name VARCHAR(48) NOT NULL, "
            "name_norm VARCHAR(48) NOT NULL UNIQUE, "
            "password_hash VARCHAR(256) DEFAULT '', "
            "owner_token VARCHAR(64) DEFAULT '', "
            "created_at DATETIME)"
        )
    )
    conn.execute(
        text(
            "CREATE TABLE IF NOT EXISTS guild_sessions ("
            "id INTEGER PRIMARY KEY, "
            "token VARCHAR(64) NOT NULL UNIQUE, "
            "guild_id INTEGER NOT NULL, "
            "is_owner INTEGER DEFAULT 0, "
            "created_at DATETIME, "
            "FOREIGN KEY(guild_id) REFERENCES guilds(id))"
        )
    )
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_guilds_name_norm ON guilds (name_norm)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_guild_sessions_token ON guild_sessions (token)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_guild_sessions_guild_id ON guild_sessions (guild_id)"))


def _ensure_owner_columns(conn) -> None:
    if _table_exists(conn, "guilds") and "owner_token" not in _columns(conn, "guilds"):
        conn.execute(text("ALTER TABLE guilds ADD COLUMN owner_token VARCHAR(64) DEFAULT ''"))
    if _table_exists(conn, "guild_sessions") and "is_owner" not in _columns(conn, "guild_sessions"):
        conn.execute(text("ALTER TABLE guild_sessions ADD COLUMN is_owner INTEGER DEFAULT 0"))


def _ensure_guild_id_columns(conn) -> None:
    for table in ("checkins", "weekly_slots"):
        if not _table_exists(conn, table):
            continue
        if "guild_id" not in _columns(conn, table):
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN guild_id INTEGER"))


def _backfill_legacy_guild(conn) -> None:
    """旧库没有公会概念：把已有打卡/周常归到「原有数据」，第一次用该名称进入时再设密码。"""
    if not _table_exists(conn, "guilds"):
        return
    orphan = False
    for table in ("checkins", "weekly_slots"):
        if _table_exists(conn, table) and "guild_id" in _columns(conn, table):
            n = conn.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE guild_id IS NULL")
            ).scalar()
            if n:
                orphan = True
                break
    if not orphan:
        return
    gid = conn.execute(
        text("SELECT id FROM guilds WHERE name_norm = :n"),
        {"n": LEGACY_GUILD_NAME},
    ).scalar()
    if not gid:
        conn.execute(
            text(
                "INSERT INTO guilds (name, name_norm, password_hash, owner_token) "
                "VALUES (:name, :norm, '', '')"
            ),
            {"name": LEGACY_GUILD_NAME, "norm": LEGACY_GUILD_NAME},
        )
        gid = conn.execute(
            text("SELECT id FROM guilds WHERE name_norm = :n"),
            {"n": LEGACY_GUILD_NAME},
        ).scalar()
    for table in ("checkins", "weekly_slots"):
        if _table_exists(conn, table) and "guild_id" in _columns(conn, table):
            conn.execute(
                text(f"UPDATE {table} SET guild_id = :gid WHERE guild_id IS NULL"),
                {"gid": gid},
            )


def _drop_if_exists(conn, name: str) -> None:
    conn.execute(text(f"DROP TABLE IF EXISTS {name}"))


def _finish_stale_rebuilds(conn) -> None:
    """上次迁移中途失败时，可能留下 *_v2 / *_v3 临时表。"""
    if _table_exists(conn, "checkins_v3"):
        if _table_exists(conn, "checkins"):
            _drop_if_exists(conn, "checkins_v3")
        else:
            conn.execute(text("ALTER TABLE checkins_v3 RENAME TO checkins"))
    if _table_exists(conn, "weekly_slots_v2"):
        if _table_exists(conn, "weekly_slots"):
            _drop_if_exists(conn, "weekly_slots_v2")
        else:
            conn.execute(text("ALTER TABLE weekly_slots_v2 RENAME TO weekly_slots"))


def _rebuild_checkin_unique(conn) -> None:
    """同一公会、同一人、同一天可打多个职业+职责；仅相同组合去重。"""
    if not _table_exists(conn, "checkins"):
        return
    names = _index_names(conn, "checkins")
    cols = _columns(conn, "checkins")
    table_sql = conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='checkins'")
    ).scalar() or ""
    if "guild_id" in cols and (
        "uq_checkin_guild_nick_date_prof_role" in names
        or "uq_checkin_guild_nick_date_prof_role" in table_sql
    ):
        return
    if "guild_id" in cols:
        orphans = conn.execute(
            text("SELECT COUNT(*) FROM checkins WHERE guild_id IS NULL")
        ).scalar()
        if orphans:
            _backfill_legacy_guild(conn)
            orphans = conn.execute(
                text("SELECT COUNT(*) FROM checkins WHERE guild_id IS NULL")
            ).scalar()
            if orphans:
                return

    duty_select = "duty" if "duty" in cols else "NULL"
    guild_select = "guild_id" if "guild_id" in cols else "NULL"
    _drop_if_exists(conn, "checkins_v3")
    conn.execute(
        text(
            """
            CREATE TABLE checkins_v3 (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                rally_date DATE NOT NULL,
                nickname VARCHAR(32) NOT NULL,
                profession_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                duty VARCHAR(16),
                created_at DATETIME,
                updated_at DATETIME,
                CONSTRAINT uq_checkin_guild_nick_date_prof_role
                    UNIQUE (guild_id, nickname, rally_date, profession_id, role_id),
                FOREIGN KEY(guild_id) REFERENCES guilds(id),
                FOREIGN KEY(profession_id) REFERENCES professions(id),
                FOREIGN KEY(role_id) REFERENCES roles(id)
            )
            """
        )
    )
    conn.execute(
        text(
            f"""
            INSERT INTO checkins_v3
                (id, guild_id, rally_date, nickname, profession_id, role_id, duty, created_at, updated_at)
            SELECT id, {guild_select}, rally_date, nickname, profession_id, role_id,
                   {duty_select}, created_at, updated_at
            FROM checkins
            WHERE {guild_select} IS NOT NULL
            """
        )
    )
    conn.execute(text("DROP TABLE checkins"))
    conn.execute(text("ALTER TABLE checkins_v3 RENAME TO checkins"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_checkins_rally_date ON checkins (rally_date)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_checkins_nickname ON checkins (nickname)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_checkins_guild_id ON checkins (guild_id)"))


def _rebuild_weekly_unique(conn) -> None:
    if not _table_exists(conn, "weekly_slots"):
        return
    names = _index_names(conn, "weekly_slots")
    cols = _columns(conn, "weekly_slots")
    table_sql = conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='weekly_slots'")
    ).scalar() or ""
    if "guild_id" in cols and (
        "uq_weekly_guild_nick_weekday" in names
        or "uq_weekly_guild_nick_weekday" in table_sql
    ):
        return
    if "guild_id" in cols:
        orphans = conn.execute(
            text("SELECT COUNT(*) FROM weekly_slots WHERE guild_id IS NULL")
        ).scalar()
        if orphans:
            _backfill_legacy_guild(conn)
            orphans = conn.execute(
                text("SELECT COUNT(*) FROM weekly_slots WHERE guild_id IS NULL")
            ).scalar()
            if orphans:
                return

    guild_select = "guild_id" if "guild_id" in cols else "NULL"
    duty_select = "duty" if "duty" in cols else "NULL"
    _drop_if_exists(conn, "weekly_slots_v2")
    conn.execute(
        text(
            """
            CREATE TABLE weekly_slots_v2 (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                nickname VARCHAR(32) NOT NULL,
                weekday INTEGER NOT NULL,
                profession_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                duty VARCHAR(16),
                CONSTRAINT uq_weekly_guild_nick_weekday
                    UNIQUE (guild_id, nickname, weekday),
                FOREIGN KEY(guild_id) REFERENCES guilds(id),
                FOREIGN KEY(profession_id) REFERENCES professions(id),
                FOREIGN KEY(role_id) REFERENCES roles(id)
            )
            """
        )
    )
    conn.execute(
        text(
            f"""
            INSERT INTO weekly_slots_v2
                (id, guild_id, nickname, weekday, profession_id, role_id, duty)
            SELECT id, {guild_select}, nickname, weekday, profession_id, role_id, {duty_select}
            FROM weekly_slots
            WHERE {guild_select} IS NOT NULL
            """
        )
    )
    conn.execute(text("DROP TABLE weekly_slots"))
    conn.execute(text("ALTER TABLE weekly_slots_v2 RENAME TO weekly_slots"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_weekly_slots_nickname ON weekly_slots (nickname)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_weekly_slots_weekday ON weekly_slots (weekday)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_weekly_slots_guild_id ON weekly_slots (guild_id)"))


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
