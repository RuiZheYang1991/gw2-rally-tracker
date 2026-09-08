<template>
  <div>
    <section class="panel">
      <h2>本周预计出勤</h2>
      <p class="hint">横轴为星期，纵轴为勾选该晚的去重人数。缺坦 / 缺 DPS / 缺辅助的格子会用红色虚线标出。</p>
      <div class="chart-box">
        <Gw2Chart v-if="barData" type="bar" :data="barData" :options="barOptions" />
      </div>
    </section>

    <div class="week-board">
      <article v-for="day in forecast.days || []" :key="day.weekday" class="panel day-col">
        <header class="day-head">
          <span>{{ day.weekday_zh }}</span>
          <strong>{{ day.unique_people }}</strong>
        </header>
        <div
          v-for="block in day.roles"
          :key="block.key"
          class="role-block"
          :class="{ vacant: block.vacant }"
        >
          <h3>
            {{ block.name_zh }}
            <em>{{ block.count }}</em>
          </h3>
          <div v-if="block.vacant" class="empty-slot">空缺</div>
          <div v-else class="prof-groups">
            <div v-for="g in block.professions" :key="g.profession_key" class="prof-group">
              <p>
                {{ block.name_zh }}-{{ g.name_zh }}
                <b>×{{ g.count }}</b>
              </p>
              <div class="nicks">
                <span v-for="n in g.nicknames" :key="n" class="nick">{{ n }}</span>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import Gw2Chart from "../components/Gw2Chart.vue";

const forecast = ref({ days: [] });

const barData = computed(() => {
  const days = forecast.value.days || [];
  if (!days.length) return null;
  return {
    labels: days.map((d) => d.weekday_zh),
    datasets: [
      {
        label: "预计人数",
        data: days.map((d) => d.unique_people),
        backgroundColor: days.map((d) =>
          d.roles.some((r) => r.vacant) ? "rgba(212,106,106,.75)" : "rgba(232,195,106,.8)"
        ),
      },
    ],
  };
});

const barOptions = {
  indexAxis: "x",
};

onMounted(async () => {
  forecast.value = await api.weeklyForecast();
});
</script>
