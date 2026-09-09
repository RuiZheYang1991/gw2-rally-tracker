import { ref } from "vue";

const TOKEN_KEY = "gw2-session";
const NAME_KEY = "gw2-guild-name";
const OWNER_PREFIX = "gw2-owner:";

export const guildName = ref(localStorage.getItem(NAME_KEY) || "");
export const isOwner = ref(false);

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function getOwnerToken(name) {
  const key = (name || guildName.value || "").trim();
  if (!key) return "";
  return localStorage.getItem(OWNER_PREFIX + key) || "";
}

export function setSession(token, name, extra = {}) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  if (name) {
    localStorage.setItem(NAME_KEY, name);
    guildName.value = name;
  }
  if (extra.isOwner != null) isOwner.value = Boolean(extra.isOwner);
  if (extra.ownerToken && (name || guildName.value)) {
    localStorage.setItem(OWNER_PREFIX + (name || guildName.value).trim(), extra.ownerToken);
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(NAME_KEY);
  guildName.value = "";
  isOwner.value = false;
}

export function isLoggedIn() {
  return Boolean(getToken());
}
