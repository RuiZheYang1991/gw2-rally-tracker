"""数据表：职业、职责、每日打卡。人数由打卡记录聚合得出。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Profession(Base):
    __tablename__ = "professions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name_zh: Mapped[str] = mapped_column(String(32))
    name_en: Mapped[str] = mapped_column(String(32))
    color: Mapped[str] = mapped_column(String(16))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    armor: Mapped[str] = mapped_column(String(16), default="heavy")
    family_key: Mapped[str] = mapped_column(String(32), default="")
    spec_kind: Mapped[str] = mapped_column(String(16), default="core")

    checkins: Mapped[list["CheckIn"]] = relationship(back_populates="profession")
    weekly_slots: Mapped[list["WeeklySlot"]] = relationship(back_populates="profession")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name_zh: Mapped[str] = mapped_column(String(32))
    name_en: Mapped[str] = mapped_column(String(32))
    color: Mapped[str] = mapped_column(String(16))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    checkins: Mapped[list["CheckIn"]] = relationship(back_populates="role")
    weekly_slots: Mapped[list["WeeklySlot"]] = relationship(back_populates="role")


class CheckIn(Base):
    """同一人同一天可登记多个职业+职责组合；相同组合只保留一条。"""

    __tablename__ = "checkins"
    __table_args__ = (
        UniqueConstraint(
            "nickname",
            "rally_date",
            "profession_id",
            "role_id",
            name="uq_checkin_nick_date_prof_role",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rally_date: Mapped[date] = mapped_column(Date, index=True)
    nickname: Mapped[str] = mapped_column(String(32), index=True)
    profession_id: Mapped[int] = mapped_column(ForeignKey("professions.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    # 冗余职责码：Tank / DPS / Support，方便按文档约定的 VARCHAR 过滤
    duty: Mapped[str] = mapped_column(String(16), default="DPS", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    profession: Mapped[Profession] = relationship(back_populates="checkins")
    role: Mapped[Role] = relationship(back_populates="checkins")


class WeeklySlot(Base):
    """成员周常空闲：每个勾选的星期只需填一套主要职业+职责。"""

    __tablename__ = "weekly_slots"
    __table_args__ = (UniqueConstraint("nickname", "weekday", name="uq_weekly_nick_weekday"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nickname: Mapped[str] = mapped_column(String(32), index=True)
    weekday: Mapped[int] = mapped_column(Integer, index=True)  # 0=周一 … 6=周日
    profession_id: Mapped[int] = mapped_column(ForeignKey("professions.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    duty: Mapped[str] = mapped_column(String(16), default="DPS")

    profession: Mapped[Profession] = relationship(back_populates="weekly_slots")
    role: Mapped[Role] = relationship(back_populates="weekly_slots")
