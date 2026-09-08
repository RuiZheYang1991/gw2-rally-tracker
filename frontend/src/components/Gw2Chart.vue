<template>
  <div class="chart-canvas-wrap">
    <canvas ref="el"></canvas>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";

Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler
);

const props = defineProps({
  type: { type: String, required: true },
  data: { type: Object, required: true },
  options: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["select"]);
const el = ref(null);
let chart;
let applying = false;
let lastFinger = "";
let resizeObs;

function fingerprint() {
  try {
    return `${props.type}:${JSON.stringify(props.data)}`;
  } catch {
    return `${props.type}:${Date.now()}`;
  }
}

function apply() {
  if (!el.value || applying) return;
  const finger = fingerprint();
  if (chart && finger === lastFinger) {
    chart.resize();
    return;
  }
  applying = true;
  lastFinger = finger;
  try {
    if (chart && chart.config.type === props.type) {
      chart.data.labels = props.data?.labels || [];
      chart.data.datasets = props.data?.datasets || [];
      chart.update("none");
      chart.resize();
      return;
    }
    chart?.destroy();
    const extra = props.options || {};
    const { onClick: extraClick, plugins: extraPlugins, ...rest } = extra;
    chart = new Chart(el.value, {
      type: props.type,
      data: {
        labels: props.data?.labels || [],
        datasets: props.data?.datasets || [],
      },
      options: {
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
            labels: { color: "#f3e6c4", font: { family: "Noto Serif SC" } },
          },
          ...extraPlugins,
        },
        scales:
          props.type === "doughnut" || props.type === "pie"
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
      },
    });
  } finally {
    applying = false;
  }
}

onMounted(async () => {
  await nextTick();
  apply();
  requestAnimationFrame(() => chart?.resize());
  if (typeof ResizeObserver !== "undefined" && el.value?.parentElement) {
    resizeObs = new ResizeObserver(() => chart?.resize());
    resizeObs.observe(el.value.parentElement);
  }
});

watch(
  () => [props.type, props.data],
  () => {
    nextTick(apply);
  },
  { deep: true }
);

onBeforeUnmount(() => {
  resizeObs?.disconnect();
  chart?.destroy();
  chart = null;
});
</script>

<style scoped>
.chart-canvas-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 280px;
}
</style>
