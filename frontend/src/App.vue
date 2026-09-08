<template>
  <div class="shell" :class="{ 'shell-wide': route.meta.wide }">
    <header class="topbar">
      <div class="brand">
        <small>Guild Wars 2 · Rally Ledger</small>
        <h1>公会集结 · 出勤账本</h1>
      </div>
      <nav class="nav">
        <button
          v-for="item in navItems"
          :key="item.to"
          type="button"
          :class="{ active: isActive(item.to) }"
          @click="go(item.to)"
        >
          {{ item.label }}
        </button>
      </nav>
    </header>
    <router-view :key="route.fullPath" />
  </div>
</template>

<script setup>
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const navItems = [
  { to: "/", label: "今晚打卡" },
  { to: "/stats", label: "出勤统计" },
  { to: "/settings", label: "周常设置" },
  { to: "/forecast", label: "周常总表" },
];

function isActive(path) {
  return path === "/" ? route.path === "/" : route.path.startsWith(path);
}

function go(path) {
  if (route.path === path) return;
  router.push(path);
}
</script>
