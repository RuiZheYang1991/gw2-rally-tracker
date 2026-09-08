const API = "";

async function parse(res) {
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
  return res.json();
}

export const api = {
  professions: () => fetch(`${API}/api/professions`).then(parse),
  roles: () => fetch(`${API}/api/roles`).then(parse),
  checkins: (rallyDate) => {
    const q = rallyDate ? `?rally_date=${rallyDate}` : "";
    return fetch(`${API}/api/checkins${q}`).then(parse);
  },
  upsertCheckin: (payload) =>
    fetch(`${API}/api/checkins`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(parse),
  deleteCheckin: (id) => fetch(`${API}/api/checkins/${id}`, { method: "DELETE" }).then(parse),
  overview: (days, end) => {
    const params = new URLSearchParams({ days: String(days) });
    if (end) params.set("end", end);
    return fetch(`${API}/api/stats/overview?${params}`).then(parse);
  },
  dayStats: (rallyDate) =>
    fetch(`${API}/api/stats/day?rally_date=${rallyDate}`).then(parse),
  weekly: (nickname) =>
    fetch(`${API}/api/weekly?nickname=${encodeURIComponent(nickname)}`).then(parse),
  saveWeekly: (payload) =>
    fetch(`${API}/api/weekly`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(parse),
  weeklyForecast: () => fetch(`${API}/api/weekly/forecast`).then(parse),
};
