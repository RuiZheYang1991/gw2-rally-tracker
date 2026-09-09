import { createRouter, createWebHistory } from "vue-router";
import CheckInView from "./views/CheckInView.vue";
import ForecastView from "./views/ForecastView.vue";
import LoginView from "./views/LoginView.vue";
import PasswordView from "./views/PasswordView.vue";
import SettingsView from "./views/SettingsView.vue";
import StatsView from "./views/StatsView.vue";
import { isLoggedIn, isOwner } from "./session";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: LoginView, meta: { public: true } },
    { path: "/", name: "checkin", component: CheckInView },
    { path: "/stats", name: "stats", component: StatsView },
    { path: "/settings", name: "settings", component: SettingsView },
    { path: "/password", name: "password", component: PasswordView, meta: { owner: true } },
    { path: "/forecast", name: "forecast", component: ForecastView, meta: { wide: true } },
  ],
});

router.beforeEach((to) => {
  if (to.meta.public) {
    if (isLoggedIn() && to.path === "/login") return "/";
    return true;
  }
  if (!isLoggedIn()) return "/login";
  if (to.meta.owner && !isOwner.value) return "/";
  return true;
});

export default router;
