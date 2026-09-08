<template>
  <section class="panel">
    <h2>每周出勤时间</h2>
    <p class="hint">勾选通常能出团的晚上，并为每一天指定主要职业 + 职责。团长在「周常总表」里会按坦 / DPS / 辅助汇总。</p>

    <label class="field">
      <span>游戏昵称</span>
      <input v-model="nickname" maxlength="32" placeholder="与打卡时相同的昵称" />
    </label>

    <div class="week-editor">
      <div v-for="day in days" :key="day.weekday" class="week-row">
        <label class="week-check">
          <input v-model="day.enabled" type="checkbox" />
          <strong>{{ day.label }}</strong>
        </label>
        <select v-model="day.profession_key" :disabled="!day.enabled">
          <option v-for="p in professionOptions" :key="p.key" :value="p.key">
            {{ p.name_zh }}
          </option>
        </select>
        <select v-model="day.role_key" :disabled="!day.enabled">
          <option v-for="r in roles" :key="r.key" :value="r.key">{{ r.name_zh }}</option>
        </select>
      </div>
    </div>

    <button class="gold-btn" :disabled="busy" @click="save">保存周常空闲</button>
    <p class="msg" :class="{ error: isError }">{{ message }}</p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { api } from "../api";
import { sortedProfessions } from "../professions";

const LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
let loadTimer;

function blankDays() {
  return LABELS.map((label, weekday) => ({
    weekday,
    label,
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
    message.value = "请填写游戏昵称";
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
    message.value = "周常空闲已更新";
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
