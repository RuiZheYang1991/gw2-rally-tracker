const API = "";

import { clearSession, getOwnerToken, getToken } from "./session";

async function parse(res) {
  if (res.status === 401) {
    clearSession();
    if (!window.location.pathname.startsWith("/login")) {
      window.location.assign("/login");
    }
  }
  if (!res.ok) {
    let detail = `请求失败 (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

function headers(extra = {}) {
  const token = getToken();
  return {
    ...extra,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export const api = {
  login: (guild_name, password) =>
    fetch(`${API}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        guild_name,
        password,
        owner_token: getOwnerToken(guild_name),
      }),
    }).then(parse),
  me: () => fetch(`${API}/api/auth/me`, { headers: headers() }).then(parse),
  logout: () =>
    fetch(`${API}/api/auth/logout`, { method: "POST", headers: headers() }).then(parse),
  changePassword: (current_password, new_password) =>
    fetch(`${API}/api/auth/password`, {
      method: "POST",
      headers: headers({ "Content-Type": "application/json" }),
      body: JSON.stringify({ current_password, new_password }),
    }).then(parse),
  professions: () => fetch(`${API}/api/professions`).then(parse),
  roles: () => fetch(`${API}/api/roles`).then(parse),
  checkins: (rallyDate) => {
    const q = rallyDate ? `?rally_date=${rallyDate}` : "";
    return fetch(`${API}/api/checkins${q}`, { headers: headers() }).then(parse);
  },
  upsertCheckin: (payload) =>
    fetch(`${API}/api/checkins`, {
      method: "POST",
      headers: headers({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    }).then(parse),
  deleteCheckin: (id) =>
    fetch(`${API}/api/checkins/${id}`, { method: "DELETE", headers: headers() }).then(parse),
  overview: (days, end) => {
    const params = new URLSearchParams({ days: String(days) });
    if (end) params.set("end", end);
    return fetch(`${API}/api/stats/overview?${params}`, { headers: headers() }).then(parse);
  },
  dayStats: (rallyDate) =>
    fetch(`${API}/api/stats/day?rally_date=${rallyDate}`, { headers: headers() }).then(parse),
  weekly: (nickname) =>
    fetch(`${API}/api/weekly?nickname=${encodeURIComponent(nickname)}`, {
      headers: headers(),
    }).then(parse),
  saveWeekly: (payload) =>
    fetch(`${API}/api/weekly`, {
      method: "PUT",
      headers: headers({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    }).then(parse),
  weeklyForecast: () =>
    fetch(`${API}/api/weekly/forecast`, { headers: headers() }).then(parse),
};
