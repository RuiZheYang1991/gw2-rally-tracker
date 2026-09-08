<template>
  <section class="panel">
    <h2>{{ t("settingsTitle") }}</h2>
    <p class="hint">{{ t("settingsHint") }}</p>

    <label class="field">
      <span>{{ t("gameNick") }}</span>
      <input v-model="nickname" maxlength="32" :placeholder="t('gameNickPh')" />
    </label>

    <div class="week-editor">
      <div v-for="day in days" :key="day.weekday" class="week-row">
        <label class="week-check">
          <input v-model="day.enabled" type="checkbox" />
          <strong>{{ weekdayLabel(day.weekday) }}</strong>
        </label>
        <select class="notranslate" v-model="day.profession_key" :disabled="!day.enabled">
          <option v-for="p in professionOptions" :key="p.key" :value="p.key">
            {{ displayName(p) }}
          </option>
        </select>
        <select class="notranslate" v-model="day.role_key" :disabled="!day.enabled">
          <option v-for="r in roles" :key="r.key" :value="r.key">{{ displayName(r) }}</option>
        </select>
      </div>
    </div>

    <button class="gold-btn" :disabled="busy" @click="save">{{ t("saveWeekly") }}</button>
    <p class="msg" :class="{ error: isError }">{{ message }}</p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { api } from "../api";
import { displayName, t, weekdayLabel } from "../i18n";
import { sortedProfessions } from "../professions";

let loadTimer;

function blankDays() {
  return [0, 1, 2, 3, 4, 5, 6].map((weekday) => ({
    weekday,
    enabled: false,
    profession_key: "revenant",
    role_key: "support",
  }));
}

const nickname = ref(sessionStorage.getItem("gw2-nick") || "");
const professions = ref([]);
const professionOptions = computed(() => sortedProfessions(professions.value));
const roles = ref([]);
const days = ref(blankDays());
const busy = ref(false);
const message = ref("");
const isError = ref(false);

async function load() {
  const nick = nickname.value.trim();
  days.value = blankDays();
  if (!nick) return;
  const data = await api.weekly(nick);
  for (const slot of data.slots || []) {
    const row = days.value[slot.weekday];
    if (!row) continue;
    row.enabled = true;
    row.profession_key = slot.profession.key;
    row.role_key = slot.role.key;
  }
}

async function save() {
  isError.value = false;
  message.value = "";
  const nick = nickname.value.trim();
  if (!nick) {
    isError.value = true;
    message.value = t("needGameNick");
    return;
  }
  busy.value = true;
  try {
    sessionStorage.setItem("gw2-nick", nick);
    await api.saveWeekly({
      nickname: nick,
      slots: days.value
        .filter((d) => d.enabled)
        .map((d) => ({
          weekday: d.weekday,
          profession_key: d.profession_key,
          role_key: d.role_key,
        })),
    });
    message.value = t("weeklySaved");
  } catch (err) {
    isError.value = true;
    message.value = err.message;
  } finally {
    busy.value = false;
  }
}

onMounted(async () => {
  professions.value = await api.professions();
  roles.value = await api.roles();
  await load();
});

watch(nickname, () => {
  clearTimeout(loadTimer);
  loadTimer = setTimeout(load, 400);
});
</script>
