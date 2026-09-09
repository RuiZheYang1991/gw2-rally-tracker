import { computed, ref } from "vue";

const STORAGE = "gw2-lang";

export const locale = ref(localStorage.getItem(STORAGE) === "en" ? "en" : "zh");

const ZH = {
  title: "激战2   战场出团打卡",
  brand: "激战2   战场出团帐本",
  navCheckin: "今晚打卡",
  navStats: "出勤统计",
  navSettings: "周常设置",
  navForecast: "周常总表",
  checkinTitle: "登记今晚职业",
  nickname: "游戏昵称",
  nickPlaceholder: "例如： sfeee",
  rallyDate: "出團日期",
  confirm: "确认出席",
  roster: "{date} 出席名册 · {people} 人 / {slots} 人次",
  undo: "撤销",
  noCheckin: "今夜尚无打卡。",
  needNick: "请填写游戏昵称",
  savedCheckin: "已记入今晚名册（可继续登记其他职业或职责）",
  armorAll: "职业",
  armorHeavy: "重甲",
  armorMedium: "中甲",
  armorLight: "轻甲",
  statsTitle: "出勤总览",
  statsHint: "饼图与柱状图以职责为主分类。点击某一职责可下钻到该职责下的职业构成。",
  statsWindow: "统计窗口",
  last7: "近 7 天",
  last30: "近 30 天",
  byDay: "按日查看",
  dailyHeadcount: "每日总出勤（去重人数）",
  roleShare: "职责占比",
  roleCount: "职责人数",
  drillHint: "点击上方职责图可切换下钻目标。",
  drillFallback: "职责下钻",
  composition: "职业构成",
  detail: "{date} 明细 · {people} 人 / {slots} 人次",
  noDay: "该日没有打卡记录。",
  matrixTitle: "窗口内职责人次",
  date: "日期",
  people: "人数",
  chartHeadcount: "出勤人数",
  chartSlots: "人次",
  vacant: "空缺",
  settingsTitle: "每周出勤时间",
  settingsHint: "勾选通常能出团的晚上，并为每一天指定主要职业与职责。团长在「周常总表」里会按职责汇总。",
  gameNick: "游戏昵称",
  gameNickPh: "与打卡时相同的昵称",
  saveWeekly: "保存周常空闲",
  needGameNick: "请填写游戏昵称",
  weeklySaved: "周常空闲已更新",
  forecastTitle: "本周预计出勤",
  forecastHint: "横轴为星期，纵轴为勾选该晚的去重人数。缺坦 / 缺 DPS / 缺辅助的格子会用红色虚线标出。",
  expected: "预计人数",
  wd0: "周一",
  wd1: "周二",
  wd2: "周三",
  wd3: "周四",
  wd4: "周五",
  wd5: "周六",
  wd6: "周日",
  loginTitle: "进入公会账本",
  loginHint: "公会长第一次填写公会名称和密码，即完成注册。之后把同一组公会名和密码发给团员，即可打卡。",
  guildName: "公会名称",
  guildNamePh: "例如：Ge",
  guildPassword: "密码",
  guildPasswordPh: "至少 4 位，首次进入即设置",
  loginEnter: "进入",
  needGuild: "请填写公会名称",
  needPassword: "请设置至少 4 位密码",
  logout: "退出",
  currentGuild: "當前公會",
  navPassword: "改密码",
  passwordTitle: "修改公会密码",
  passwordHint: "改完后请把新密码发给团员。其他人需要重新进入。",
  passwordCurrent: "当前密码",
  passwordNew: "新密码",
  passwordConfirm: "再输入一次新密码",
  passwordSave: "保存新密码",
  passwordMismatch: "两次新密码不一致",
  passwordSaved: "密码已更新，请把新密码发给团员",
};

const EN = {
  title: "Guild Rally · Check-in",
  brand: "Guild Rally · Attendance Ledger",
  navCheckin: "Check-in",
  navStats: "Stats",
  navSettings: "Weekly Setup",
  navForecast: "Weekly Board",
  checkinTitle: "Tonight's profession",
  nickname: "Game ID",
  nickPlaceholder: "e.g. Specter",
  rallyDate: "Rally date",
  confirm: "Confirm attendance",
  roster: "{date} roster · {people} players / {slots} slots",
  undo: "Undo",
  noCheckin: "No check-ins for this night.",
  needNick: "Please enter a Game ID",
  savedCheckin: "Saved. You can add another profession or role.",
  armorAll: "Professions",
  armorHeavy: "Heavy",
  armorMedium: "Medium",
  armorLight: "Light",
  statsTitle: "Attendance overview",
  statsHint: "Charts are grouped by role (DPS / Support / Tank). Click a role to see professions inside it.",
  statsWindow: "Range",
  last7: "Last 7 days",
  last30: "Last 30 days",
  byDay: "By day",
  dailyHeadcount: "Daily unique attendance",
  roleShare: "Role share",
  roleCount: "Role counts",
  drillHint: "Click a role chart above to change the breakdown.",
  drillFallback: "Role drill-down",
  composition: "profession mix",
  detail: "{date} detail · {people} players / {slots} slots",
  noDay: "No check-ins on this day.",
  matrixTitle: "Role slots in range",
  date: "Date",
  people: "Players",
  chartHeadcount: "Players",
  chartSlots: "Slots",
  vacant: "Vacant",
  settingsTitle: "Weekly availability",
  settingsHint: "Pick nights you usually raid, and set profession + role for each. Commanders see this on the Weekly Board.",
  gameNick: "In-game name",
  gameNickPh: "Same nickname as check-in",
  saveWeekly: "Save weekly slots",
  needGameNick: "Please enter an in-game name",
  weeklySaved: "Weekly availability saved",
  forecastTitle: "Expected weekly attendance",
  forecastHint: "Bars are unique players per weekday. Missing Tank / DPS / Support is outlined in red dashes.",
  expected: "Expected players",
  wd0: "Mon",
  wd1: "Tue",
  wd2: "Wed",
  wd3: "Thu",
  wd4: "Fri",
  wd5: "Sat",
  wd6: "Sun",
  loginTitle: "Enter guild ledger",
  loginHint: "The first time a guild name is used, that password creates the guild. Share the same name and password with members so they can check in.",
  guildName: "Guild name",
  guildNamePh: "e.g. Ge",
  guildPassword: "Password",
  guildPasswordPh: "At least 4 characters; set on first login",
  loginEnter: "Enter",
  needGuild: "Please enter a guild name",
  needPassword: "Please set a password of at least 4 characters",
  logout: "Log out",
  currentGuild: "Current guild",
  navPassword: "Password",
  passwordTitle: "Change guild password",
  passwordHint: "Share the new password with members. Others will need to sign in again.",
  passwordCurrent: "Current password",
  passwordNew: "New password",
  passwordConfirm: "Confirm new password",
  passwordSave: "Save password",
  passwordMismatch: "New passwords do not match",
  passwordSaved: "Password updated. Share the new one with members.",
};

const BAG = { zh: ZH, en: EN };

export const isEn = computed(() => locale.value === "en");

export function t(key, vars = {}) {
  let text = BAG[locale.value]?.[key] ?? ZH[key] ?? key;
  for (const [k, v] of Object.entries(vars)) {
    text = text.replaceAll(`{${k}}`, String(v));
  }
  return text;
}

export function setLocale(next) {
  locale.value = next === "en" ? "en" : "zh";
  localStorage.setItem(STORAGE, locale.value);
  document.documentElement.lang = locale.value === "en" ? "en" : "zh-CN";
  document.title = t("title");
}

/** Official EN names from API — do not run through machine translation. */
export function displayName(item) {
  if (!item) return "";
  if (locale.value === "en") return item.name_en || item.name_zh || "";
  return item.name_zh || item.name_en || "";
}

export function weekdayLabel(index) {
  return t(`wd${index}`);
}

export function applyDocumentLang() {
  document.documentElement.lang = locale.value === "en" ? "en" : "zh-CN";
  document.title = t("title");
}
