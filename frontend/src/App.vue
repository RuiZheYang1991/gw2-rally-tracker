<template>
  <div class="shell" :class="{ 'shell-wide': route.meta.wide, 'shell-login': route.meta.public }">
    <header class="topbar">
      <div class="lang-switch" role="group" :aria-label="t('title')">
        <button type="button" :class="{ active: locale === 'zh' }" @click="setLocale('zh')">中</button>
        <button type="button" :class="{ active: locale === 'en' }" @click="setLocale('en')">EN</button>
      </div>
      <div class="brand">
        <small>Guild Wars 2 · Rally Ledger</small>
        <h1>{{ t("brand") }}</h1>
        <p v-if="guildName" class="guild-chip notranslate">{{ guildName }}</p>
      </div>
      <div class="topbar-right">
        <nav v-if="!route.meta.public" class="nav">
          <button
            v-for="item in navItems"
            :key="item.to"
            type="button"
            :class="{ active: isActive(item.to) }"
            @click="go(item.to)"
          >
            {{ item.label }}
          </button>
          <button
            v-if="isOwner"
            type="button"
            :class="{ active: isActive('/password') }"
            @click="go('/password')"
          >
            {{ t("navPassword") }}
          </button>
          <button type="button" class="nav-logout" @click="logout">{{ t("logout") }}</button>
        </nav>
      </div>
    </header>
    <router-view :key="route.fullPath" />
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "./api";
import { locale, setLocale, t } from "./i18n";
import { clearSession, guildName, isOwner, setSession } from "./session";

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

async function logout() {
  try {
    await api.logout();
  } catch {
    /* ignore */
  }
  clearSession();
  router.replace("/login");
}

onMounted(async () => {
  if (route.meta.public) return;
  try {
    const me = await api.me();
    if (me?.guild_name) {
      setSession("", me.guild_name, { isOwner: me.is_owner, ownerToken: me.owner_token });
    }
  } catch {
    /* 401 already redirects */
  }
});
</script>
