import { createRouter, createWebHistory } from "vue-router";
import CheckInView from "./views/CheckInView.vue";
import StatsView from "./views/StatsView.vue";
import SettingsView from "./views/SettingsView.vue";
import ForecastView from "./views/ForecastView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "checkin", component: CheckInView },
    { path: "/stats", name: "stats", component: StatsView },
    { path: "/settings", name: "settings", component: SettingsView },
    { path: "/forecast", name: "forecast", component: ForecastView, meta: { wide: true } },
  ],
});
