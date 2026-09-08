"""请求/响应模型。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class ProfessionOut(BaseModel):
    key: str
    name_zh: str
    name_en: str
    color: str
    sort_order: int
    armor: str = "heavy"
    family_key: str = ""
    spec_kind: str = "core"

    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    key: str
    name_zh: str
    name_en: str
    color: str
    sort_order: int

    model_config = {"from_attributes": True}


class CheckInCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=32)
    profession_key: str
    role_key: str
    rally_date: date | None = None


class CheckInOut(BaseModel):
    id: int
    rally_date: date
    nickname: str
    profession: ProfessionOut
    role: RoleOut
    duty: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CountItem(BaseModel):
    key: str
    name_zh: str
    color: str
    count: int
    duty: str | None = None


class DailyTotal(BaseModel):
    date: date
    total: int
    slots: int = 0


class DayProfessionCount(BaseModel):
    date: date
    profession_key: str
    name_zh: str
    color: str
    count: int


class DayRoleCount(BaseModel):
    date: date
    role_key: str
    name_zh: str
    color: str
    duty: str
    count: int


class OverviewStats(BaseModel):
    days: int
    start_date: date
    end_date: date
    daily_totals: list[DailyTotal]
    by_profession: list[CountItem]
    by_role: list[CountItem]
    by_day_profession: list[DayProfessionCount]
    by_day_role: list[DayRoleCount] = []


class RoleProfessionSlice(BaseModel):
    profession_key: str
    name_zh: str
    color: str
    count: int
    nicknames: list[str]


class RoleDrilldown(BaseModel):
    key: str
    name_zh: str
    color: str
    duty: str
    count: int
    professions: list[RoleProfessionSlice]


class DayStats(BaseModel):
    date: date
    total: int
    slots: int
    by_profession: list[CountItem]
    by_role: list[CountItem]
    by_role_detail: list[RoleDrilldown]
    checkins: list[CheckInOut]


class WeeklySlotIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    profession_key: str
    role_key: str


class WeeklyPut(BaseModel):
    nickname: str = Field(min_length=1, max_length=32)
    slots: list[WeeklySlotIn]


class WeeklySlotOut(BaseModel):
    weekday: int
    weekday_zh: str
    profession: ProfessionOut
    role: RoleOut
    duty: str


class WeeklyMemberOut(BaseModel):
    nickname: str
    slots: list[WeeklySlotOut]


class ForecastProfessionGroup(BaseModel):
    profession_key: str
    name_zh: str
    color: str
    count: int
    nicknames: list[str]


class ForecastRoleBlock(BaseModel):
    key: str
    name_zh: str
    color: str
    duty: str
    count: int
    vacant: bool
    professions: list[ForecastProfessionGroup]


class ForecastDay(BaseModel):
    weekday: int
    weekday_zh: str
    unique_people: int
    roles: list[ForecastRoleBlock]


class WeeklyForecast(BaseModel):
    days: list[ForecastDay]
