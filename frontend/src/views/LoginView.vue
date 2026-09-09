<template>
  <section class="panel login-panel">
    <h2>{{ t("loginTitle") }}</h2>
    <p class="hint">{{ t("loginHint") }}</p>

    <form @submit.prevent="submit">
      <label class="field">
        <span>{{ t("guildName") }}</span>
        <input
          v-model="name"
          maxlength="48"
          autocomplete="username"
          :placeholder="t('guildNamePh')"
        />
      </label>
      <label class="field">
        <span>{{ t("guildPassword") }}</span>
        <input
          v-model="password"
          type="password"
          maxlength="64"
          autocomplete="current-password"
          :placeholder="t('guildPasswordPh')"
        />
      </label>
      <button class="gold-btn" type="submit" :disabled="busy">{{ t("loginEnter") }}</button>
      <p class="msg" :class="{ error: isError }">{{ message }}</p>
    </form>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { t } from "../i18n";
import { setSession } from "../session";

const router = useRouter();
const name = ref("");
const password = ref("");
const busy = ref(false);
const message = ref("");
const isError = ref(false);

async function submit() {
  const guildName = name.value.trim();
  if (!guildName) {
    isError.value = true;
    message.value = t("needGuild");
    return;
  }
  if (password.value.trim().length < 4) {
    isError.value = true;
    message.value = t("needPassword");
    return;
  }
  busy.value = true;
  isError.value = false;
  message.value = "";
  try {
    const out = await api.login(guildName, password.value);
    setSession(out.token, out.guild_name, {
      isOwner: out.is_owner,
      ownerToken: out.owner_token,
    });
    await router.replace("/");
  } catch (err) {
    isError.value = true;
    message.value = err.message;
  } finally {
    busy.value = false;
  }
}
</script>
