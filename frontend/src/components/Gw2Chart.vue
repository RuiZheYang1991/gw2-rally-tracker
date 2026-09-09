<template>
  <div class="chart-canvas-wrap">
    <canvas ref="el"></canvas>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Chart from "chart.js/auto";

const props = defineProps({
  type: { type: String, required: true },
  data: { type: Object, required: true },
  options: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["select"]);
const el = ref(null);
let chart = null;

function cloneData(data) {
  try {
    return JSON.parse(JSON.stringify(data || { labels: [], datasets: [] }));
  } catch {
    return { labels: [], datasets: [] };
  }
}

function snapshot() {
  try {
    return `${props.type}:${JSON.stringify(props.data)}`;
  } catch {
    return `${props.type}:invalid`;
  }
}

function buildOptions() {
  const extra = props.options || {};
  const { onClick: extraClick, plugins: extraPlugins, ...rest } = extra;
  const isRound = props.type === "doughnut" || props.type === "pie";
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    ...rest,
    onClick(event, elements) {
      extraClick?.(event, elements);
      if (elements?.length) emit("select", elements[0].index);
    },
    plugins: {
      legend: {
        labels: { color: "#f3e6c4", font: { family: "Noto Serif SC, serif" } },
      },
      ...extraPlugins,
    },
    scales: isRound
      ? rest.scales
      : rest.scales || {
          x: {
            ticks: { color: "#b7a88a" },
            grid: { color: "rgba(232,195,106,.12)" },
          },
          y: {
            beginAtZero: true,
            ticks: { color: "#b7a88a", precision: 0 },
            grid: { color: "rgba(232,195,106,.12)" },
          },
        },
  };
}

function apply() {
  if (!el.value) return;
  const data = cloneData(props.data);
  try {
    if (!chart || chart.config.type !== props.type) {
      chart?.destroy();
      chart = new Chart(el.value, {
        type: props.type,
        data,
        options: buildOptions(),
      });
      return;
    }
    chart.data.labels = data.labels || [];
    chart.data.datasets = data.datasets || [];
    chart.update("none");
  } catch (err) {
    console.error("Gw2Chart", err);
  }
}

onMounted(async () => {
  await nextTick();
  apply();
  requestAnimationFrame(() => chart?.resize());
});

watch(snapshot, () => nextTick(apply));

onBeforeUnmount(() => {
  chart?.destroy();
  chart = null;
});
</script>

<style scoped>
.chart-canvas-wrap {
  position: relative;
  width: 100%;
  height: 300px;
}

.chart-canvas-wrap canvas {
  display: block;
}
</style>
