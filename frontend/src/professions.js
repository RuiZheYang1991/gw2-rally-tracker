export const ARMOR_GROUPS = [
  { armor: "heavy", label: "重甲" },
  { armor: "medium", label: "中甲" },
  { armor: "light", label: "轻甲" },
];

/** 核心职业 key → 其下全部独立职业（含特化）。不依赖后端是否回传 family_key。 */
const FAMILIES = {
  warrior: ["warrior", "berserker", "spellbreaker", "bladesworn", "paragon"],
  guardian: ["guardian", "dragonhunter", "firebrand", "willbender", "luminary"],
  revenant: ["revenant", "herald", "renegade", "vindicator", "conduit"],
  engineer: ["engineer", "scrapper", "holosmith", "mechanist", "amalgam"],
  ranger: ["ranger", "druid", "soulbeast", "untamed", "galeshot"],
  thief: ["thief", "daredevil", "deadeye", "specter"],
  elementalist: ["elementalist", "tempest", "weaver", "catalyst", "evoker"],
  mesmer: ["mesmer", "chronomancer", "mirage", "virtuoso", "troubadour"],
  necromancer: ["necromancer", "reaper", "scourge", "harbinger", "ritualist"],
};

const ARMOR_BY_FAMILY = {
  warrior: "heavy",
  guardian: "heavy",
  revenant: "heavy",
  engineer: "medium",
  ranger: "medium",
  thief: "medium",
  elementalist: "light",
  mesmer: "light",
  necromancer: "light",
};

const FAMILY_ORDER = Object.keys(FAMILIES);

const FAMILY_BY_KEY = Object.fromEntries(
  Object.entries(FAMILIES).flatMap(([family, keys]) => keys.map((key) => [key, family]))
);

function familyOf(p) {
  return p.family_key || FAMILY_BY_KEY[p.key] || p.key;
}

function armorOf(p) {
  return p.armor || ARMOR_BY_FAMILY[familyOf(p)] || "heavy";
}

export function groupProfessions(list) {
  const byKey = Object.fromEntries(list.map((p) => [p.key, p]));
  return ARMOR_GROUPS.map((meta) => {
    const families = FAMILY_ORDER.filter((fk) => ARMOR_BY_FAMILY[fk] === meta.armor)
      .map((fk) => {
        const members = FAMILIES[fk].map((key) => byKey[key]).filter(Boolean);
        return {
          key: fk,
          core: members.find((m) => m.spec_kind === "core" || m.key === fk) || members[0],
          specs: members.filter((m) => m.key !== fk),
          members,
        };
      })
      .filter((f) => f.members.length);
    return { ...meta, families };
  }).filter((g) => g.families.length);
}

/** 核心在前、特化紧随其后，当作独立选项使用。 */
export function sortedProfessions(list) {
  const grouped = groupProfessions(list);
  if (grouped.length) {
    return grouped.flatMap((g) => g.families.flatMap((f) => f.members));
  }
  return list.slice().sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
}

export { familyOf, armorOf };
