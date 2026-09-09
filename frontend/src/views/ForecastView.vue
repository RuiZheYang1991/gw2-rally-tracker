<template>
  <div>
    <section class="panel">
      <h2>{{ t("forecastTitle") }}</h2>
      <p class="hint">{{ t("forecastHint") }}</p>
      <div class="chart-box">
        <Gw2Chart v-if="barData" type="bar" :data="barData" :options="barOptions" />
      </div>
    </section>

    <div class="week-board">
      <article v-for="day in forecast.days || []" :key="day.weekday" class="panel day-col">
        <header class="day-head">
          <span>{{ weekdayLabel(day.weekday) }}</span>
          <strong>{{ day.unique_people }}</strong>
        </header>
        <div
          v-for="block in day.roles"
          :key="block.key"
          class="role-block"
          :class="{ vacant: block.vacant }"
        >
          <h3>
            <span class="notranslate">{{ displayName(matchRole(block)) }}</span>
            <em>{{ block.count }}</em>
          </h3>
          <div v-if="block.vacant" class="empty-slot">{{ t("vacant") }}</div>
          <div v-else class="prof-groups">
            <div v-for="g in block.professions" :key="g.profession_key" class="prof-group">
              <p class="notranslate">
                {{ displayName(matchRole(block)) }}-{{ displayName(matchProf(g)) }}
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
import { displayName, locale, t, weekdayLabel } from "../i18n";

const forecast = ref({ days: [] });
const roles = ref([]);
const professions = ref([]);

function matchRole(item) {
  return roles.value.find((r) => r.key === item.key) || item;
}

function matchProf(item) {
  return professions.value.find((p) => p.key === item.profession_key) || item;
}

const barData = computed(() => {
  locale.value;
  const days = forecast.value.days || [];
  if (!days.length) return null;
  return {
    labels: days.map((d) => weekdayLabel(d.weekday)),
    datasets: [
      {
        label: t("expected"),
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
  roles.value = await api.roles();
  professions.value = await api.professions();
  forecast.value = await api.weeklyForecast();
});
</script>
