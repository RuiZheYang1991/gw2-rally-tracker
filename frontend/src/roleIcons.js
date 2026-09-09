import iconDps from "./assets/roles/dps.png";
import iconSupport from "./assets/roles/support.png";
import iconTank from "./assets/roles/tank.png";

export const ROLE_ICONS = {
  dps: iconDps,
  support: iconSupport,
  tank: iconTank,
};

export function roleIcon(key) {
  return ROLE_ICONS[key] || iconDps;
}
