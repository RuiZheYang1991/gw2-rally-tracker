/** 占位纹章：特化复用核心职业外形，后期按 key 替换官方图标即可。 */
const PATHS = {
  guardian: "M32 6 L54 16 V36 C54 48 44 56 32 60 C20 56 10 48 10 36 V16 Z M32 16 V50 M22 28 H42",
  warrior: "M12 50 L32 8 L52 50 H12 Z M20 38 H44",
  engineer: "M32 10 L38 22 H50 L40 30 L44 44 L32 36 L20 44 L24 30 L14 22 H26 Z",
  ranger: "M32 8 C20 20 16 34 32 56 C48 34 44 20 32 8 Z M32 22 V40",
  thief: "M18 44 L32 8 L46 44 M24 32 H40",
  elementalist: "M32 8 L48 32 L32 56 L16 32 Z M32 20 L40 32 L32 44 L24 32 Z",
  mesmer: "M12 32 Q32 4 52 32 Q32 60 12 32 Z M24 32 Q32 20 40 32 Q32 44 24 32 Z",
  necromancer: "M32 10 C22 10 16 20 16 30 C16 46 32 56 32 56 C32 56 48 46 48 30 C48 20 42 10 32 10 Z M32 24 V42",
  revenant: "M10 18 H54 L44 48 H20 Z M32 18 V48",
};

export function professionMark(key, color = "#E8A317", familyKey = "") {
  const d = PATHS[key] || PATHS[familyKey] || PATHS.guardian;
  return `<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <circle cx="32" cy="32" r="30" fill="rgba(0,0,0,.45)" stroke="${color}" stroke-width="2"/>
    <path d="${d}" fill="none" stroke="${color}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>
  </svg>`;
}
