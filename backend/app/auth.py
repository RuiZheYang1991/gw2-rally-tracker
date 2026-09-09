"""公会名 + 密码登录。第一次使用会创建公会并记下密码。"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import Guild, GuildSession

PBKDF2_ROUNDS = 120_000
MIN_PASSWORD = 4
MAX_GUILD_NAME = 48


def normalize_guild_name(raw: str) -> str:
    return " ".join((raw or "").strip().split())


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ROUNDS
    ).hex()
    return f"pbkdf2${PBKDF2_ROUNDS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        kind, rounds_s, salt, digest = stored.split("$", 3)
        if kind != "pbkdf2":
            return False
        rounds = int(rounds_s)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), rounds
    ).hex()
    return hmac.compare_digest(check, digest)


def issue_session(db: Session, guild: Guild, *, is_owner: bool = False) -> str:
    token = secrets.token_urlsafe(32)
    db.add(GuildSession(token=token, guild_id=guild.id, is_owner=is_owner))
    db.commit()
    return token


def ensure_owner_token(guild: Guild) -> str:
    if not guild.owner_token:
        guild.owner_token = secrets.token_urlsafe(32)
    return guild.owner_token


def owner_token_matches(guild: Guild, candidate: str) -> bool:
    stored = guild.owner_token or ""
    given = (candidate or "").strip()
    if not stored or not given or len(stored) != len(given):
        return False
    return hmac.compare_digest(stored, given)


def parse_bearer(authorization: str | None) -> str:
    if not authorization:
        return ""
    parts = authorization.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return authorization.strip()


def get_current_session(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> GuildSession:
    token = parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="请先用公会名称和密码进入")
    row = (
        db.query(GuildSession)
        .filter(GuildSession.token == token)
        .first()
    )
    if not row:
        raise HTTPException(status_code=401, detail="登录已失效，请重新进入")
    guild = db.query(Guild).filter(Guild.id == row.guild_id).first()
    if not guild:
        raise HTTPException(status_code=401, detail="登录已失效，请重新进入")
    return row


def get_current_guild(
    session: GuildSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> Guild:
    guild = db.query(Guild).filter(Guild.id == session.guild_id).first()
    if not guild:
        raise HTTPException(status_code=401, detail="登录已失效，请重新进入")
    return guild
