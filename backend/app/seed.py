"""激战2 核心九职业 + 精英特化（含即将推出）。后续加条目只需扩展 PROFESSIONS。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Profession, Role


def _p(key, name_zh, name_en, family, armor, kind, color, order):
    return {
        "key": key,
        "name_zh": name_zh,
        "name_en": name_en,
        "family_key": family,
        "armor": armor,
        "spec_kind": kind,
        "color": color,
        "sort_order": order,
    }


# 甲种色板沿用核心职业色，特化略作明暗变化便于区分
W, G, R = "#FFD166", "#72C1D9", "#D16E5A"
E, N, T = "#D09C59", "#8CDC82", "#C08CA0"
EL, M, NE = "#F68A87", "#B679D5", "#52A76F"

PROFESSIONS = [
    # 重甲 · 士兵
    _p("warrior", "战士", "Warrior", "warrior", "heavy", "core", W, 100),
    _p("berserker", "狂战士", "Berserker", "warrior", "heavy", "elite", "#E8B84A", 101),
    _p("spellbreaker", "破法者", "Spellbreaker", "warrior", "heavy", "elite", "#F0C878", 102),
    _p("bladesworn", "刃枪士", "Bladesworn", "warrior", "heavy", "elite", "#C9A227", 103),
    _p("paragon", "圣言士", "Paragon", "warrior", "heavy", "upcoming", "#FFE6A0", 104),
    _p("guardian", "守护者", "Guardian", "guardian", "heavy", "core", G, 110),
    _p("dragonhunter", "龙魂使", "Dragonhunter", "guardian", "heavy", "elite", "#5BA8C4", 111),
    _p("firebrand", "炎使", "Firebrand", "guardian", "heavy", "elite", "#8FD4E8", 112),
    _p("willbender", "毅行者", "Willbender", "guardian", "heavy", "elite", "#4E90B0", 113),
    _p("luminary", "流明使", "Luminary", "guardian", "heavy", "upcoming", "#B8E8F4", 114),
    _p("revenant", "魂武者", "Revenant", "revenant", "heavy", "core", R, 120),
    _p("herald", "先知", "Herald", "revenant", "heavy", "elite", "#E08A78", 121),
    _p("renegade", "叛乱者", "Renegade", "revenant", "heavy", "elite", "#B85A48", 122),
    _p("vindicator", "判官", "Vindicator", "revenant", "heavy", "elite", "#C97A68", 123),
    _p("conduit", "契灵使", "Conduit", "revenant", "heavy", "upcoming", "#F0A898", 124),
    # 中甲 · 冒险家
    _p("engineer", "工程师", "Engineer", "engineer", "medium", "core", E, 200),
    _p("scrapper", "机械师", "Scrapper", "engineer", "medium", "elite", "#B8894A", 201),
    _p("holosmith", "全息师", "Holosmith", "engineer", "medium", "elite", "#E0B070", 202),
    _p("mechanist", "机械使", "Mechanist", "engineer", "medium", "elite", "#C4A06A", 203),
    _p("amalgam", "流金师", "Amalgam", "engineer", "medium", "upcoming", "#F0D0A0", 204),
    _p("ranger", "游侠", "Ranger", "ranger", "medium", "core", N, 210),
    _p("druid", "德鲁伊", "Druid", "ranger", "medium", "elite", "#6BC46A", 211),
    _p("soulbeast", "魂兽师", "Soulbeast", "ranger", "medium", "elite", "#A8E89A", 212),
    _p("untamed", "狂兽师", "Untamed", "ranger", "medium", "elite", "#4E9A52", 213),
    _p("galeshot", "风羽者", "Galeshot", "ranger", "medium", "upcoming", "#C8F0B8", 214),
    _p("thief", "潜行者", "Thief", "thief", "medium", "core", T, 220),
    _p("daredevil", "独行侠", "Daredevil", "thief", "medium", "elite", "#A07088", 221),
    _p("deadeye", "神枪手", "Deadeye", "thief", "medium", "elite", "#D4A0B4", 222),
    _p("specter", "缚影者", "Specter", "thief", "medium", "elite", "#8A5A78", 223),
    # 轻甲 · 学者
    _p("elementalist", "元素使", "Elementalist", "elementalist", "light", "core", EL, 300),
    _p("tempest", "暴风使", "Tempest", "elementalist", "light", "elite", "#E07070", 301),
    _p("weaver", "编织者", "Weaver", "elementalist", "light", "elite", "#F4A8A4", 302),
    _p("catalyst", "元晶师", "Catalyst", "elementalist", "light", "elite", "#C85C60", 303),
    _p("evoker", "唤元师", "Evoker", "elementalist", "light", "upcoming", "#FFC4C0", 304),
    _p("mesmer", "幻术师", "Mesmer", "mesmer", "light", "core", M, 310),
    _p("chronomancer", "时空术士", "Chronomancer", "mesmer", "light", "elite", "#9A58C4", 311),
    _p("mirage", "幻象术士", "Mirage", "mesmer", "light", "elite", "#D09AE8", 312),
    _p("virtuoso", "灵刃术士", "Virtuoso", "mesmer", "light", "elite", "#7A40A8", 313),
    _p("troubadour", "吟游诗人", "Troubadour", "mesmer", "light", "upcoming", "#E8C4F4", 314),
    _p("necromancer", "死灵法师", "Necromancer", "necromancer", "light", "core", NE, 320),
    _p("reaper", "夺魂者", "Reaper", "necromancer", "light", "elite", "#3E8A58", 321),
    _p("scourge", "灾厄师", "Scourge", "necromancer", "light", "elite", "#6EBF88", 322),
    _p("harbinger", "先驱者", "Harbinger", "necromancer", "light", "elite", "#2E6A44", 323),
    _p("ritualist", "祭祀者", "Ritualist", "necromancer", "light", "upcoming", "#98D4A8", 324),
]

# key 存库；duty 对外固定为 Tank / DPS / Support
ROLES = [
    {"key": "tank", "name_zh": "坦", "name_en": "Tank", "color": "#C45C5C", "sort_order": 1},
    {"key": "dps", "name_zh": "DPS", "name_en": "DPS", "color": "#E8A317", "sort_order": 2},
    {"key": "support", "name_zh": "辅助", "name_en": "Support", "color": "#7EC8E3", "sort_order": 3},
]

DUTY_BY_KEY = {"tank": "Tank", "dps": "DPS", "support": "Support"}


def seed_lookups(db: Session) -> None:
    existing_prof = {row.key: row for row in db.query(Profession).all()}
    for item in PROFESSIONS:
        row = existing_prof.get(item["key"])
        if not row:
            db.add(Profession(**item))
        else:
            row.name_zh = item["name_zh"]
            row.name_en = item["name_en"]
            row.color = item["color"]
            row.sort_order = item["sort_order"]
            row.armor = item["armor"]
            row.family_key = item["family_key"]
            row.spec_kind = item["spec_kind"]

    existing_role = {row.key: row for row in db.query(Role).all()}
    for item in ROLES:
        row = existing_role.get(item["key"])
        if not row:
            db.add(Role(**item))
        else:
            row.name_zh = item["name_zh"]
            row.name_en = item["name_en"]
            row.color = item["color"]
            row.sort_order = item["sort_order"]

    db.commit()
