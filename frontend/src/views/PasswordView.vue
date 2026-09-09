<template>
  <section class="panel login-panel">
    <h2>{{ t("passwordTitle") }}</h2>
    <p class="hint">{{ t("passwordHint") }}</p>

    <form @submit.prevent="submit">
      <label class="field">
        <span>{{ t("passwordCurrent") }}</span>
        <input v-model="current" type="password" maxlength="64" autocomplete="current-password" />
      </label>
      <label class="field">
        <span>{{ t("passwordNew") }}</span>
        <input v-model="next" type="password" maxlength="64" autocomplete="new-password" />
      </label>
      <label class="field">
        <span>{{ t("passwordConfirm") }}</span>
        <input v-model="confirm" type="password" maxlength="64" autocomplete="new-password" />
      </label>
      <button class="gold-btn" type="submit" :disabled="busy">{{ t("passwordSave") }}</button>
      <p class="msg" :class="{ error: isError }">{{ message }}</p>
    </form>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { api } from "../api";
import { t } from "../i18n";

const current = ref("");
const next = ref("");
const confirm = ref("");
const busy = ref(false);
const message = ref("");
const isError = ref(false);

async function submit() {
  if (current.value.trim().length < 4 || next.value.trim().length < 4) {
    isError.value = true;
    message.value = t("needPassword");
    return;
  }
  if (next.value !== confirm.value) {
    isError.value = true;
    message.value = t("passwordMismatch");
    return;
  }
  busy.value = true;
  isError.value = false;
  message.value = "";
  try {
    await api.changePassword(current.value, next.value);
    current.value = "";
    next.value = "";
    confirm.value = "";
    message.value = t("passwordSaved");
  } catch (err) {
    isError.value = true;
    message.value = err.message;
  } finally {
    busy.value = false;
  }
}
</script>
