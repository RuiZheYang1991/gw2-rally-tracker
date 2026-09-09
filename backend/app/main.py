"""公会集结出勤 API。"""

from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .auth import (
    MAX_GUILD_NAME,
    MIN_PASSWORD,
    ensure_owner_token,
    get_current_guild,
    get_current_session,
    hash_password,
    issue_session,
    normalize_guild_name,
    owner_token_matches,
    parse_bearer,
    verify_password,
)
from .database import Base, engine, get_db
from .migrate import migrate_schema
from .models import CheckIn, Guild, GuildSession, Profession, Role, WeeklySlot
from .schemas import (
    AuthLogin,
    AuthOut,
    PasswordChange,
    CheckInCreate,
    CheckInOut,
    CountItem,
    DailyTotal,
    DayProfessionCount,
    DayRoleCount,
    DayStats,
    ForecastDay,
    ForecastProfessionGroup,
    ForecastRoleBlock,
    OverviewStats,
    ProfessionOut,
    RoleDrilldown,
    RoleOut,
    RoleProfessionSlice,
    WeeklyForecast,
    WeeklyMemberOut,
    WeeklyPut,
    WeeklySlotOut,
)
from .seed import DUTY_BY_KEY, seed_lookups

WEEKDAY_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    migrate_schema(engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_lookups(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="GW2 Rally Tracker",
    description="公会每晚集结：职业打卡、职责统计与周常预测",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """浏览器请打开前端；8000 只提供 JSON API。"""
    return {
        "service": "GW2 Rally Tracker API",
        "ui": "http://127.0.0.1:5173",
        "docs": "/docs",
        "health": "/api/health",
    }


def duty_of(role: Role) -> str:
    return DUTY_BY_KEY.get(role.key, role.name_en)


def serialize_checkin(row: CheckIn) -> CheckInOut:
    return CheckInOut(
        id=row.id,
        rally_date=row.rally_date,
        nickname=row.nickname.strip(),
        profession=ProfessionOut.model_validate(row.profession),
        role=RoleOut.model_validate(row.role),
        duty=row.duty or duty_of(row.role),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def date_window(days: int, end: date | None = None) -> tuple[date, date]:
    end_date = end or date.today()
    start_date = end_date - timedelta(days=days - 1)
    return start_date, end_date


def lookup_spec(db: Session, profession_key: str, role_key: str) -> tuple[Profession, Role]:
    profession = db.query(Profession).filter(Profession.key == profession_key).first()
    role = db.query(Role).filter(Role.key == role_key).first()
    if not profession:
        raise HTTPException(status_code=400, detail="未知职业")
    if not role:
        raise HTTPException(status_code=400, detail="未知职责")
    return profession, role


def role_drilldown(db: Session, rows: list[CheckIn]) -> list[RoleDrilldown]:
    roles = db.query(Role).order_by(Role.sort_order).all()
    professions = db.query(Profession).order_by(Profession.sort_order).all()
    grouped: dict[str, dict[str, list[CheckIn]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row.role.key][row.profession.key].append(row)

    result = []
    for role in roles:
        slices = []
        total = 0
        for prof in professions:
            bucket = grouped[role.key].get(prof.key, [])
            if not bucket:
                continue
            total += len(bucket)
            slices.append(
                RoleProfessionSlice(
                    profession_key=prof.key,
                    name_zh=prof.name_zh,
                    color=prof.color,
                    count=len(bucket),
                    nicknames=[x.nickname for x in bucket],
                )
            )
        result.append(
            RoleDrilldown(
                key=role.key,
                name_zh=role.name_zh,
                color=role.color,
                duty=duty_of(role),
                count=total,
                professions=slices,
            )
        )
    return result


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=AuthOut)
def login(payload: AuthLogin, db: Session = Depends(get_db)):
    name = normalize_guild_name(payload.guild_name)
    password = (payload.password or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="请填写公会名称")
    if len(name) > MAX_GUILD_NAME:
        raise HTTPException(status_code=400, detail="公会名称过长")
    if len(password) < MIN_PASSWORD:
        raise HTTPException(status_code=400, detail="密码至少 4 位")

    name_norm = name.casefold()
    guild = db.query(Guild).filter(Guild.name_norm == name_norm).first()
    created = False
    if guild is None:
        guild = Guild(name=name, name_norm=name_norm, password_hash=hash_password(password))
        db.add(guild)
        db.commit()
        db.refresh(guild)
        created = True
    elif not guild.password_hash:
        guild.password_hash = hash_password(password)
        db.commit()
        created = True
    elif not verify_password(password, guild.password_hash):
        raise HTTPException(status_code=401, detail="公会名称或密码不对")

    is_owner = created or owner_token_matches(guild, payload.owner_token)
    if created:
        ensure_owner_token(guild)
        db.commit()
    token = issue_session(db, guild, is_owner=is_owner)
    return AuthOut(
        token=token,
        guild_name=guild.name,
        created=created,
        is_owner=is_owner,
        owner_token=guild.owner_token if is_owner else "",
    )


@app.get("/api/auth/me", response_model=AuthOut)
def auth_me(
    db: Session = Depends(get_db),
    session: GuildSession = Depends(get_current_session),
    guild: Guild = Depends(get_current_guild),
):
    claimed = False
    if not (guild.owner_token or "").strip():
        ensure_owner_token(guild)
        session.is_owner = True
        db.commit()
        claimed = True
    is_owner = bool(session.is_owner) or claimed
    return AuthOut(
        guild_name=guild.name,
        created=False,
        is_owner=is_owner,
        owner_token=guild.owner_token if is_owner else "",
    )


@app.post("/api/auth/password")
def change_password(
    payload: PasswordChange,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    session: GuildSession = Depends(get_current_session),
    guild: Guild = Depends(get_current_guild),
):
    if not session.is_owner:
        raise HTTPException(status_code=403, detail="只有公会创建者可以改密码")
    current = (payload.current_password or "").strip()
    new = (payload.new_password or "").strip()
    if len(new) < MIN_PASSWORD:
        raise HTTPException(status_code=400, detail="新密码至少 4 位")
    if current == new:
        raise HTTPException(status_code=400, detail="新密码不能与当前密码相同")
    if not verify_password(current, guild.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不对")
    guild.password_hash = hash_password(new)
    keep = parse_bearer(authorization)
    q = db.query(GuildSession).filter(GuildSession.guild_id == guild.id)
    if keep:
        q = q.filter(GuildSession.token != keep)
    q.delete(synchronize_session=False)
    db.commit()
    return {"ok": True}


@app.post("/api/auth/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    token = parse_bearer(authorization)
    if token:
        db.query(GuildSession).filter(GuildSession.token == token).delete()
        db.commit()
    return {"ok": True}


@app.get("/api/professions", response_model=list[ProfessionOut])
def list_professions(db: Session = Depends(get_db)):
    return db.query(Profession).order_by(Profession.sort_order).all()


@app.get("/api/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).order_by(Role.sort_order).all()


@app.post("/api/checkins", response_model=CheckInOut)
def upsert_checkin(
    payload: CheckInCreate,
    db: Session = Depends(get_db),
    guild: Guild = Depends(get_current_guild),
):
    nickname = payload.nickname.strip()
    if not nickname:
        raise HTTPException(status_code=400, detail="昵称不能为空")

    rally_date = payload.rally_date or date.today()
    profession, role = lookup_spec(db, payload.profession_key, payload.role_key)

    existing = (
        db.query(CheckIn)
        .options(joinedload(CheckIn.profession), joinedload(CheckIn.role))
        .filter(
            CheckIn.guild_id == guild.id,
            CheckIn.nickname == nickname,
            CheckIn.rally_date == rally_date,
            CheckIn.profession_id == profession.id,
            CheckIn.role_id == role.id,
        )
        .first()
    )
    if existing:
        existing.duty = duty_of(role)
        db.commit()
        db.refresh(existing)
        return serialize_checkin(existing)

    row = CheckIn(
        guild_id=guild.id,
        nickname=nickname,
        rally_date=rally_date,
        profession_id=profession.id,
        role_id=role.id,
        duty=duty_of(role),
    )
    db.add(row)
    db.commit()
    row = (
        db.query(CheckIn)
        .options(joinedload(CheckIn.profession), joinedload(CheckIn.role))
        .filter(CheckIn.id == row.id)
        .one()
    )
    return serialize_checkin(row)


@app.get("/api/checkins", response_model=list[CheckInOut])
def list_checkins(
    rally_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    guild: Guild = Depends(get_current_guild),
):
    query = (
        db.query(CheckIn)
        .options(joinedload(CheckIn.profession), joinedload(CheckIn.role))
        .filter(CheckIn.guild_id == guild.id)
    )
    if rally_date:
        query = query.filter(CheckIn.rally_date == rally_date)
    rows = query.order_by(CheckIn.created_at.asc()).all()
    return [serialize_checkin(row) for row in rows]


@app.delete("/api/checkins/{checkin_id}")
def delete_checkin(
    checkin_id: int,
    db: Session = Depends(get_db),
    guild: Guild = Depends(get_current_guild),
):
    row = (
        db.query(CheckIn)
        .filter(CheckIn.id == checkin_id, CheckIn.guild_id == guild.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/stats/overview", response_model=OverviewStats)
def overview(
    days: int = Query(default=7, ge=1, le=90),
    end: date | None = Query(default=None),
    db: Session = Depends(get_db),
    guild: Guild = Depends(get_current_guild),
):
    start_date, end_date = date_window(days, end)
    guild_scope = CheckIn.guild_id == guild.id

    daily_people = (
        db.query(CheckIn.rally_date, func.count(func.distinct(CheckIn.nickname)))
        .filter(guild_scope, CheckIn.rally_date >= start_date, CheckIn.rally_date <= end_date)
        .group_by(CheckIn.rally_date)
        .all()
    )
    daily_slots = (
        db.query(CheckIn.rally_date, func.count(CheckIn.id))
        .filter(guild_scope, CheckIn.rally_date >= start_date, CheckIn.rally_date <= end_date)
        .group_by(CheckIn.rally_date)
        .all()
    )
    people_map = {d: c for d, c in daily_people}
    slot_map = {d: c for d, c in daily_slots}
    daily_totals = []
    cursor = start_date
    while cursor <= end_date:
        daily_totals.append(
            DailyTotal(
                date=cursor,
                total=people_map.get(cursor, 0),
                slots=slot_map.get(cursor, 0),
            )
        )
        cursor += timedelta(days=1)

    prof_rows = (
        db.query(Profession, func.count(CheckIn.id))
        .outerjoin(
            CheckIn,
            (CheckIn.profession_id == Profession.id)
            & (CheckIn.guild_id == guild.id)
            & (CheckIn.rally_date >= start_date)
            & (CheckIn.rally_date <= end_date),
        )
        .group_by(Profession.id)
        .order_by(Profession.sort_order)
        .all()
    )
    by_profession = [
        CountItem(key=p.key, name_zh=p.name_zh, color=p.color, count=c) for p, c in prof_rows
    ]

    role_rows = (
        db.query(Role, func.count(CheckIn.id))
        .outerjoin(
            CheckIn,
            (CheckIn.role_id == Role.id)
            & (CheckIn.guild_id == guild.id)
            & (CheckIn.rally_date >= start_date)
            & (CheckIn.rally_date <= end_date),
        )
        .group_by(Role.id)
        .order_by(Role.sort_order)
        .all()
    )
    by_role = [
        CountItem(key=r.key, name_zh=r.name_zh, color=r.color, count=c, duty=duty_of(r))
        for r, c in role_rows
    ]

    day_prof_rows = (
        db.query(CheckIn.rally_date, Profession, func.count(CheckIn.id))
        .join(Profession, CheckIn.profession_id == Profession.id)
        .filter(CheckIn.guild_id == guild.id, CheckIn.rally_date >= start_date, CheckIn.rally_date <= end_date)
        .group_by(CheckIn.rally_date, Profession.id)
        .order_by(CheckIn.rally_date, Profession.sort_order)
        .all()
    )
    by_day_profession = [
        DayProfessionCount(
            date=d,
            profession_key=p.key,
            name_zh=p.name_zh,
            color=p.color,
            count=c,
        )
        for d, p, c in day_prof_rows
    ]

    day_role_rows = (
        db.query(CheckIn.rally_date, Role, func.count(CheckIn.id))
        .join(Role, CheckIn.role_id == Role.id)
        .filter(CheckIn.guild_id == guild.id, CheckIn.rally_date >= start_date, CheckIn.rally_date <= end_date)
        .group_by(CheckIn.rally_date, Role.id)
        .order_by(CheckIn.rally_date, Role.sort_order)
        .all()
    )
    by_day_role = [
        DayRoleCount(
            date=d,
            role_key=r.key,
            name_zh=r.name_zh,
            color=r.color,
            duty=duty_of(r),
            count=c,
        )
        for d, r, c in day_role_rows
    ]

    return OverviewStats(
        days=days,
        start_date=start_date,
        end_date=end_date,
        daily_totals=daily_totals,
        by_profession=by_profession,
        by_role=by_role,
        by_day_profession=by_day_profession,
        by_day_role=by_day_role,
    )


@app.get("/api/stats/day", response_model=DayStats)
def day_stats(
    rally_date: date = Query(...),
    db: Session = Depends(get_db),
    guild: Guild = Depends(get_current_guild),
):
    rows = (
        db.query(CheckIn)
        .options(joinedload(CheckIn.profession), joinedload(CheckIn.role))
        .filter(CheckIn.guild_id == guild.id, CheckIn.rally_date == rally_date)
        .order_by(CheckIn.created_at.asc())
        .all()
    )
    detail = role_drilldown(db, rows)
    professions = db.query(Profession).order_by(Profession.sort_order).all()
    prof_map: dict[str, CountItem] = {}
    for row in rows:
        p = row.profession
        if p.key not in prof_map:
            prof_map[p.key] = CountItem(key=p.key, name_zh=p.name_zh, color=p.color, count=0)
        prof_map[p.key].count += 1

    return DayStats(
        date=rally_date,
        total=len({row.nickname for row in rows}),
        slots=len(rows),
        by_profession=[
            prof_map.get(p.key, CountItem(key=p.key, name_zh=p.name_zh, color=p.color, count=0))
            for p in professions
        ],
        by_role=[
            CountItem(key=b.key, name_zh=b.name_zh, color=b.color, count=b.count, duty=b.duty)
            for b in detail
        ],
        by_role_detail=detail,
        checkins=[serialize_checkin(row) for row in rows],
    )


def serialize_slot(row: WeeklySlot) -> WeeklySlotOut:
    return WeeklySlotOut(
        weekday=row.weekday,
        weekday_zh=WEEKDAY_ZH[row.weekday],
        profession=ProfessionOut.model_validate(row.profession),
        role=RoleOut.model_validate(row.role),
        duty=row.duty or duty_of(row.role),
    )


@app.get("/api/weekly", response_model=WeeklyMemberOut)
def get_weekly(
    nickname: str = Query(..., min_length=1, max_length=32),
    db: Session = Depends(get_db),
    guild: Guild = Depends(get_current_guild),
):
    nick = nickname.strip()
    rows = (
        db.query(WeeklySlot)
        .options(joinedload(WeeklySlot.profession), joinedload(WeeklySlot.role))
        .filter(WeeklySlot.guild_id == guild.id, WeeklySlot.nickname == nick)
        .order_by(WeeklySlot.weekday)
        .all()
    )
    return WeeklyMemberOut(nickname=nick, slots=[serialize_slot(r) for r in rows])


@app.put("/api/weekly", response_model=WeeklyMemberOut)
def put_weekly(
    payload: WeeklyPut,
    db: Session = Depends(get_db),
    guild: Guild = Depends(get_current_guild),
):
    nick = payload.nickname.strip()
    if not nick:
        raise HTTPException(status_code=400, detail="昵称不能为空")

    seen = set()
    prepared = []
    for slot in payload.slots:
        if slot.weekday in seen:
            raise HTTPException(status_code=400, detail="同一星期只能填一套主要职责")
        seen.add(slot.weekday)
        profession, role = lookup_spec(db, slot.profession_key, slot.role_key)
        prepared.append((slot.weekday, profession, role))

    db.query(WeeklySlot).filter(WeeklySlot.guild_id == guild.id, WeeklySlot.nickname == nick).delete()
    for weekday, profession, role in prepared:
        db.add(
            WeeklySlot(
                guild_id=guild.id,
                nickname=nick,
                weekday=weekday,
                profession_id=profession.id,
                role_id=role.id,
                duty=duty_of(role),
            )
        )
    db.commit()
    return get_weekly(nickname=nick, db=db, guild=guild)


@app.get("/api/weekly/forecast", response_model=WeeklyForecast)
def weekly_forecast(
    db: Session = Depends(get_db),
    guild: Guild = Depends(get_current_guild),
):
    rows = (
        db.query(WeeklySlot)
        .options(joinedload(WeeklySlot.profession), joinedload(WeeklySlot.role))
        .filter(WeeklySlot.guild_id == guild.id)
        .all()
    )
    roles = db.query(Role).order_by(Role.sort_order).all()
    professions = db.query(Profession).order_by(Profession.sort_order).all()

    by_day: dict[int, list[WeeklySlot]] = defaultdict(list)
    for row in rows:
        by_day[row.weekday].append(row)

    days = []
    for weekday in range(7):
        day_rows = by_day.get(weekday, [])
        people = {r.nickname for r in day_rows}
        role_blocks = []
        for role in roles:
            role_rows = [r for r in day_rows if r.role_id == role.id]
            groups = []
            for prof in professions:
                nicknames = [r.nickname for r in role_rows if r.profession_id == prof.id]
                if not nicknames:
                    continue
                groups.append(
                    ForecastProfessionGroup(
                        profession_key=prof.key,
                        name_zh=prof.name_zh,
                        color=prof.color,
                        count=len(nicknames),
                        nicknames=nicknames,
                    )
                )
            role_blocks.append(
                ForecastRoleBlock(
                    key=role.key,
                    name_zh=role.name_zh,
                    color=role.color,
                    duty=duty_of(role),
                    count=len(role_rows),
                    vacant=len(role_rows) == 0,
                    professions=groups,
                )
            )
        days.append(
            ForecastDay(
                weekday=weekday,
                weekday_zh=WEEKDAY_ZH[weekday],
                unique_people=len(people),
                roles=role_blocks,
            )
        )
    return WeeklyForecast(days=days)
