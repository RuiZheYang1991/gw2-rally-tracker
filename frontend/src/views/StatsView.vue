<template>
  <div>
    <section class="panel">
      <h2>{{ t("statsTitle") }}</h2>
      <p class="hint">{{ t("statsHint") }}</p>
      <div class="toolbar">
        <label class="field">
          <span>{{ t("statsWindow") }}</span>
          <select v-model.number="days">
            <option :value="7">{{ t("last7") }}</option>
            <option :value="30">{{ t("last30") }}</option>
          </select>
        </label>
        <label class="field">
          <span>{{ t("byDay") }}</span>
          <input v-model="dayDate" type="date" />
        </label>
      </div>
    </section>

    <div class="charts" style="margin-top: 16px">
      <section class="panel">
        <h2>{{ t("dailyHeadcount") }}</h2>
        <div class="chart-box">
          <Gw2Chart v-if="lineData" type="line" :data="lineData" />
        </div>
      </section>
      <section class="panel">
        <h2>{{ dayDate }} {{ t("roleShare") }}</h2>
        <div class="chart-box">
          <Gw2Chart v-if="pieRole" type="doughnut" :data="pieRole" @select="onRoleSlice" />
        </div>
      </section>
      <section class="panel">
        <h2>{{ dayDate }} {{ t("roleCount") }}</h2>
        <div class="chart-box">
          <Gw2Chart v-if="barRole" type="bar" :data="barRole" @select="onRoleSlice" />
        </div>
      </section>
      <section class="panel">
        <h2>{{ drillTitle }}</h2>
        <p v-if="selectedRole" class="hint">{{ t("drillHint") }}</p>
        <div class="chart-box">
          <Gw2Chart v-if="pieDrill" type="doughnut" :data="pieDrill" />
        </div>
      </section>
    </div>

    <section class="panel" style="margin-top: 16px">
      <h2>{{ t("detail", { date: dayDate, people: day.total || 0, slots: day.slots || 0 }) }}</h2>
      <ul v-if="day.checkins?.length" class="roster">
        <li v-for="row in day.checkins" :key="row.id">
          <span>{{ row.nickname }}</span>
          <span class="notranslate">{{ displayName(row.role) }} · {{ displayName(row.profession) }}</span>
          <span></span>
        </li>
      </ul>
      <p v-else class="hint">{{ t("noDay") }}</p>
    </section>

    <section class="panel" style="margin-top: 16px">
      <h2>{{ t("matrixTitle") }}</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{{ t("date") }}</th>
              <th v-for="r in roles" :key="r.key" class="notranslate">{{ displayName(r) }}</th>
              <th>{{ t("people") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in matrix" :key="row.date">
              <td>{{ row.date }}</td>
              <td v-for="r in roles" :key="r.key">{{ row.counts[r.key] || 0 }}</td>
              <td>{{ row.total }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { api } from "../api";
import Gw2Chart from "../components/Gw2Chart.vue";
import { displayName, locale, t } from "../i18n";

function today() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function dateLabel(value) {
  const text = String(value || "");
  return text.length >= 10 ? text.slice(5, 10) : text;
}

const days = ref(7);
const dayDate = ref(today());
const overview = ref(null);
const day = ref({ total: 0, slots: 0, checkins: [], by_role: [], by_role_detail: [] });
const roles = ref([]);
const professions = ref([]);
const selectedRole = ref("support");

function matchRole(item) {
  return roles.value.find((r) => r.key === item.key) || item;
}

function matchProf(item) {
  const key = item.profession_key || item.key;
  return professions.value.find((p) => p.key === key) || item;
}

const lineData = computed(() => {
  if (!overview.value) return null;
  const labels = overview.value.daily_totals.map((x) => dateLabel(x.date));
  const values = overview.value.daily_totals.map((x) => x.total);
  return {
    labels,
    datasets: [
      {
        label: t("chartHeadcount"),
        data: values,
        borderColor: "#e8c36a",
        backgroundColor: "rgba(232,195,106,.18)",
        fill: true,
        tension: 0.25,
        pointBackgroundColor: "#ffd98a",
      },
    ],
  };
});

const roleItems = computed(() => day.value.by_role || []);

const pieRole = computed(() => {
  const items = roleItems.value;
  if (!items.length) return null;
  locale.value;
  return {
    labels: items.map((x) => displayName(matchRole(x))),
    datasets: [
      {
        data: items.map((x) => x.count),
        backgroundColor: items.map((x) => x.color),
        borderColor: "#121528",
      },
    ],
  };
});

const barRole = computed(() => {
  const items = roleItems.value;
  if (!items.length) return null;
  locale.value;
  return {
    labels: items.map((x) => displayName(matchRole(x))),
    datasets: [
      {
        label: t("chartSlots"),
        data: items.map((x) => x.count),
        backgroundColor: items.map((x) => x.color),
      },
    ],
  };
});

const drillBlock = computed(() => {
  const list = day.value.by_role_detail || [];
  return list.find((x) => x.key === selectedRole.value) || list[0] || null;
});

const drillTitle = computed(() => {
  if (!drillBlock.value) return t("drillFallback");
  return `${displayName(matchRole(drillBlock.value))} · ${t("composition")}`;
});

const pieDrill = computed(() => {
  locale.value;
  const block = drillBlock.value;
  if (!block) return null;
  const items = block.professions || [];
  if (!items.length) {
    return {
      labels: [t("vacant")],
      datasets: [{ data: [1], backgroundColor: ["#3a2a2a"], borderColor: "#121528" }],
    };
  }
  return {
    labels: items.map((x) => `${displayName(matchProf(x))} ×${x.count}`),
    datasets: [
      {
        data: items.map((x) => x.count),
        backgroundColor: items.map((x) => x.color),
        borderColor: "#121528",
      },
    ],
  };
});

const matrix = computed(() => {
  if (!overview.value) return [];
  const map = {};
  for (const item of overview.value.by_day_role || []) {
    if (!map[item.date]) map[item.date] = {};
    map[item.date][item.role_key] = item.count;
  }
  return overview.value.daily_totals.map((d) => ({
    date: d.date,
    counts: map[d.date] || {},
    total: d.total,
  }));
});

function onRoleSlice(index) {
  const item = roleItems.value[index];
  if (item) selectedRole.value = item.key;
}

async function loadOverview() {
  overview.value = await api.overview(days.value);
}

async function loadDay() {
  day.value = await api.dayStats(dayDate.value);
  const filled = (day.value.by_role_detail || []).find((x) => x.count > 0);
  if (filled) selectedRole.value = filled.key;
}

onMounted(async () => {
  roles.value = await api.roles();
  professions.value = await api.professions();
  await loadOverview();
  await loadDay();
});

watch(days, loadOverview);
watch(dayDate, loadDay);
</script>
