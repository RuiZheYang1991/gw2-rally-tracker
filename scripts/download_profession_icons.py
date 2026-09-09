"""从 GW2 Wiki 下载职业图标到 frontend/public/img/professions/。"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "gw2-rally-tracker/1.0 (https://github.com/RuiZheYang1991/gw2-rally-tracker; profession icon fetch)"
API = "https://wiki.guildwars2.com/api.php"
OUT = Path(__file__).resolve().parents[1] / "frontend" / "public" / "img" / "professions"

# 与 seed.py 的 key 对齐
PROFESSIONS = [
    ("warrior", "Warrior"),
    ("berserker", "Berserker"),
    ("spellbreaker", "Spellbreaker"),
    ("bladesworn", "Bladesworn"),
    ("paragon", "Paragon"),
    ("guardian", "Guardian"),
    ("dragonhunter", "Dragonhunter"),
    ("firebrand", "Firebrand"),
    ("willbender", "Willbender"),
    ("luminary", "Luminary"),
    ("revenant", "Revenant"),
    ("herald", "Herald"),
    ("renegade", "Renegade"),
    ("vindicator", "Vindicator"),
    ("conduit", "Conduit"),
    ("engineer", "Engineer"),
    ("scrapper", "Scrapper"),
    ("holosmith", "Holosmith"),
    ("mechanist", "Mechanist"),
    ("amalgam", "Amalgam"),
    ("ranger", "Ranger"),
    ("druid", "Druid"),
    ("soulbeast", "Soulbeast"),
    ("untamed", "Untamed"),
    ("galeshot", "Galeshot"),
    ("thief", "Thief"),
    ("daredevil", "Daredevil"),
    ("deadeye", "Deadeye"),
    ("specter", "Specter"),
    ("antiquary", "Antiquary"),
    ("elementalist", "Elementalist"),
    ("tempest", "Tempest"),
    ("weaver", "Weaver"),
    ("catalyst", "Catalyst"),
    ("evoker", "Evoker"),
    ("mesmer", "Mesmer"),
    ("chronomancer", "Chronomancer"),
    ("mirage", "Mirage"),
    ("virtuoso", "Virtuoso"),
    ("troubadour", "Troubadour"),
    ("necromancer", "Necromancer"),
    ("reaper", "Reaper"),
    ("scourge", "Scourge"),
    ("harbinger", "Harbinger"),
    ("ritualist", "Ritualist"),
]


def wiki_get(params: dict) -> dict:
    params = {**params, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def file_url(title: str) -> str | None:
    data = wiki_get(
        {
            "action": "query",
            "titles": f"File:{title}",
            "prop": "imageinfo",
            "iiprop": "url",
        }
    )
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = page.get("imageinfo")
        if info:
            return info[0].get("url")
    return None


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())


def candidates(wiki_name: str) -> list[str]:
    return [
        f"{wiki_name} icon (highres).png",
        f"{wiki_name} icon (unofficial color).png",
        f"{wiki_name} tango icon 200px.png",
        f"{wiki_name} icon small.png",
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ok, fail = 0, []
    for key, name in PROFESSIONS:
        dest = OUT / f"{key}.png"
        saved = False
        for title in candidates(name):
            url = file_url(title)
            time.sleep(0.15)
            if not url:
                continue
            download(url, dest)
            print(f"OK {key} <- {title}")
            saved = True
            ok += 1
            break
        if not saved:
            fail.append(key)
            print(f"FAIL {key}")
    print(f"done {ok}/{len(PROFESSIONS)} missing={fail}")
    (OUT / "SOURCE.txt").write_text(
        "Icons from Guild Wars 2 Wiki (https://wiki.guildwars2.com/wiki/Guild_Wars_2_Wiki:Profession_icons)\n"
        "Prefer highres / unofficial color / tango 200px / small colorized.\n"
        "ArenaNet / GW2 Wiki license terms apply; do not claim as original artwork.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
