<template>
  <div class="layout">
    <section class="panel">
      <h2>{{ t("checkinTitle") }}</h2>
      <p class="hint">{{ t("checkinHint") }}</p>

      <label class="field">
        <span>{{ t("nickname") }}</span>
        <input v-model="nickname" maxlength="32" :placeholder="t('nickPlaceholder')" />
      </label>
      <label class="field">
        <span>{{ t("rallyDate") }}</span>
        <input v-model="rallyDate" type="date" />
      </label>

      <div class="roles">
        <button
          v-for="r in roles"
          :key="r.key"
          type="button"
          class="role-card notranslate"
          :class="{ active: roleKey === r.key }"
          @click="roleKey = r.key"
        >
          <strong>{{ displayName(r) }}</strong>
          <em v-if="locale === 'zh'">{{ r.name_en }}</em>
        </button>
      </div>

      <div class="armor-list">
        <section v-for="group in armorGroups" :key="group.armor" class="armor-block">
          <h3>{{ group.label }}</h3>
          <div v-for="family in group.families" :key="family.key" class="grid-prof">
            <button
              v-for="p in family.members"
              :key="p.key"
              type="button"
              class="prof-card"
              :class="{
                active: professionKey === p.key,
                upcoming: p.spec_kind === 'upcoming',
              }"
              @click="professionKey = p.key"
            >
              <ProfessionIcon
                :profession-key="p.key"
                :family-key="p.family_key"
                :color="p.color"
              />
              <strong class="notranslate">{{ displayName(p) }}</strong>
            </button>
          </div>
        </section>
      </div>

      <button class="gold-btn" :disabled="busy" @click="submit">{{ t("confirm") }}</button>
      <p class="msg" :class="{ error: isError }">{{ message }}</p>
    </section>

    <section class="panel">
      <h2>{{ t("roster", { date: rallyDate, people: uniquePeople, slots: roster.length }) }}</h2>
      <ul v-if="roster.length" class="roster">
        <li v-for="row in roster" :key="row.id">
          <span>{{ row.nickname }}</span>
          <span class="notranslate">{{ displayName(row.profession) }} · {{ displayName(row.role) }}</span>
          <button class="ghost" type="button" @click="remove(row)">{{ t("undo") }}</button>
        </li>
      </ul>
      <p v-else class="hint">{{ t("noCheckin") }}</p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { api } from "../api";
import ProfessionIcon from "../components/ProfessionIcon.vue";
import { groupProfessions } from "../professions";
import { displayName, locale, t } from "../i18n";

function today() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

const nickname = ref(sessionStorage.getItem("gw2-nick") || "");
const rallyDate = ref(today());
const professionKey = ref("mesmer");
const roleKey = ref("dps");
const professions = ref([]);
const roles = ref([]);
const roster = ref([]);
const uniquePeople = computed(() => new Set(roster.value.map((r) => r.nickname)).size);
const armorGroups = computed(() => {
  const grouped = groupProfessions(professions.value);
  const labels = {
    heavy: t("armorHeavy"),
    medium: t("armorMedium"),
    light: t("armorLight"),
  };
  if (grouped.length) {
    return grouped.map((g) => ({ ...g, label: labels[g.armor] || g.label }));
  }
  return [
    {
      armor: "all",
      label: t("armorAll"),
      families: [{ key: "all", members: professions.value }],
    },
  ];
});
const busy = ref(false);
const message = ref("");
const isError = ref(false);

async function loadMeta() {
  professions.value = await api.professions();
  roles.value = await api.roles();
}

async function loadRoster() {
  roster.value = await api.checkins(rallyDate.value);
}

async function submit() {
  isError.value = false;
  message.value = "";
  if (!nickname.value.trim()) {
    isError.value = true;
    message.value = t("needNick");
    return;
  }
  busy.value = true;
  try {
    sessionStorage.setItem("gw2-nick", nickname.value.trim());
    await api.upsertCheckin({
      nickname: nickname.value.trim(),
      profession_key: professionKey.value,
      role_key: roleKey.value,
      rally_date: rallyDate.value,
    });
    message.value = t("savedCheckin");
    await loadRoster();
  } catch (err) {
    isError.value = true;
    message.value = err.message;
  } finally {
    busy.value = false;
  }
}

async function remove(row) {
  await api.deleteCheckin(row.id);
  await loadRoster();
}

onMounted(async () => {
  await loadMeta();
  await loadRoster();
});

watch(rallyDate, loadRoster);
</script>
