<template>
  <div>
    <section class="panel">
      <h2>出勤总览</h2>
      <p class="hint">饼图与柱状图以职责（坦 / DPS / 辅助）为主分类。点击某一职责可下钻到该职责下的职业构成。</p>
      <div class="toolbar">
        <label class="field">
          <span>统计窗口</span>
          <select v-model.number="days">
            <option :value="7">近 7 天</option>
            <option :value="30">近 30 天</option>
          </select>
        </label>
        <label class="field">
          <span>按日查看</span>
          <input v-model="dayDate" type="date" />
        </label>
      </div>
    </section>

    <div class="charts" style="margin-top: 16px">
      <section class="panel">
        <h2>每日总出勤（去重人数）</h2>
        <div class="chart-box">
          <Gw2Chart v-if="lineData" :key="'line-' + days" type="line" :data="lineData" />
        </div>
      </section>
      <section class="panel">
        <h2>{{ dayDate }} 职责占比</h2>
        <div class="chart-box">
          <Gw2Chart v-if="pieRole" :key="'pie-' + dayDate" type="doughnut" :data="pieRole" @select="onRoleSlice" />
        </div>
      </section>
      <section class="panel">
        <h2>{{ dayDate }} 职责人数</h2>
        <div class="chart-box">
          <Gw2Chart v-if="barRole" :key="'bar-' + dayDate" type="bar" :data="barRole" @select="onRoleSlice" />
        </div>
      </section>
      <section class="panel">
        <h2>{{ drillTitle }}</h2>
        <p v-if="selectedRole" class="hint">点击上方职责图可切换下钻目标。</p>
        <div class="chart-box">
          <Gw2Chart v-if="pieDrill" :key="'drill-' + dayDate + '-' + selectedRole" type="doughnut" :data="pieDrill" />
        </div>
      </section>
    </div>

    <section class="panel" style="margin-top: 16px">
      <h2>{{ dayDate }} 明细 · {{ day.total || 0 }} 人 / {{ day.slots || 0 }} 人次</h2>
      <ul v-if="day.checkins?.length" class="roster">
        <li v-for="row in day.checkins" :key="row.id">
          <span>{{ row.nickname }}</span>
          <span>{{ row.role.name_zh }} · {{ row.profession.name_zh }}</span>
          <span></span>
        </li>
      </ul>
      <p v-else class="hint">该日没有打卡记录。</p>
    </section>

    <section class="panel" style="margin-top: 16px">
      <h2>窗口内职责人次</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>日期</th>
              <th v-for="r in roles" :key="r.key">{{ r.name_zh }}</th>
              <th>人数</th>
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
const selectedRole = ref("support");

const lineData = computed(() => {
  if (!overview.value) return null;
  const labels = overview.value.daily_totals.map((x) => dateLabel(x.date));
  const values = overview.value.daily_totals.map((x) => x.total);
  return {
    labels,
    datasets: [
      {
        label: "出勤人数",
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
  return {
    labels: items.map((x) => x.name_zh),
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
  return {
    labels: items.map((x) => x.name_zh),
    datasets: [
      {
        label: "人次",
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
  if (!drillBlock.value) return "职责下钻";
  return `${drillBlock.value.name_zh} · 职业构成`;
});

const pieDrill = computed(() => {
  const block = drillBlock.value;
  if (!block) return null;
  const items = block.professions || [];
  if (!items.length) {
    return {
      labels: ["空缺"],
      datasets: [{ data: [1], backgroundColor: ["#3a2a2a"], borderColor: "#121528" }],
    };
  }
  return {
    labels: items.map((x) => `${x.name_zh} ×${x.count}`),
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
  await loadOverview();
  await loadDay();
});

watch(days, loadOverview);
watch(dayDate, loadDay);
</script>
