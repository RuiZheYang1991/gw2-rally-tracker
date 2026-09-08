<template>
  <div class="shell" :class="{ 'shell-wide': route.meta.wide }">
    <header class="topbar">
      <div class="brand">
        <small>Guild Wars 2 · Rally Ledger</small>
        <h1>{{ t("brand") }}</h1>
      </div>
      <div class="topbar-right">
        <div class="lang-switch" role="group" :aria-label="t('title')">
          <button type="button" :class="{ active: locale === 'zh' }" @click="setLocale('zh')">中</button>
          <button type="button" :class="{ active: locale === 'en' }" @click="setLocale('en')">EN</button>
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
      </div>
    </header>
    <router-view :key="route.fullPath" />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { locale, setLocale, t } from "./i18n";

const route = useRoute();
const router = useRouter();

const navItems = computed(() => [
  { to: "/", label: t("navCheckin") },
  { to: "/stats", label: t("navStats") },
  { to: "/settings", label: t("navSettings") },
  { to: "/forecast", label: t("navForecast") },
]);

function isActive(path) {
  return path === "/" ? route.path === "/" : route.path.startsWith(path);
}

function go(path) {
  if (route.path === path) return;
  router.push(path);
}
</script>
