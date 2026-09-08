<template>
  <div class="layout">
    <section class="panel">
      <h2>登记今晚职业</h2>
      <p class="hint">核心与特化都是独立职业，选一个即可。同一人可提交多条不同组合。虚线为即将推出的特化。</p>

      <label class="field">
        <span>公会昵称</span>
        <input v-model="nickname" maxlength="32" placeholder="例如：影织者" />
      </label>
      <label class="field">
        <span>集会日期</span>
        <input v-model="rallyDate" type="date" />
      </label>

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
              <strong>{{ p.name_zh }}</strong>
              <em>{{ specKindLabel(p) }}</em>
            </button>
          </div>
        </section>
      </div>

      <div class="roles">
        <button
          v-for="r in roles"
          :key="r.key"
          type="button"
          class="role-card"
          :class="{ active: roleKey === r.key }"
          @click="roleKey = r.key"
        >
          <strong>{{ r.name_zh }}</strong>
          <em>{{ r.name_en }}</em>
        </button>
      </div>

      <button class="gold-btn" :disabled="busy" @click="submit">确认出席</button>
      <p class="msg" :class="{ error: isError }">{{ message }}</p>
    </section>

    <section class="panel">
      <h2>{{ rallyDate }} 出席名册 · {{ uniquePeople }} 人 / {{ roster.length }} 人次</h2>
      <ul v-if="roster.length" class="roster">
        <li v-for="row in roster" :key="row.id">
          <span>{{ row.nickname }}</span>
          <span>{{ row.profession.name_zh }} · {{ row.role.name_zh }}</span>
          <button class="ghost" type="button" @click="remove(row)">撤销</button>
        </li>
      </ul>
      <p v-else class="hint">今夜尚无打卡。</p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { api } from "../api";
import ProfessionIcon from "../components/ProfessionIcon.vue";
import { groupProfessions } from "../professions";

function specKindLabel(p) {
  if (p.spec_kind === "upcoming") return "即将";
  if (p.spec_kind === "elite") return "特化";
  return "核心";
}

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
  if (grouped.length) return grouped;
  return [
    {
      armor: "all",
      label: "职业",
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
    message.value = "请填写公会昵称";
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
    message.value = "已记入今晚名册（可继续登记其他职业或职责）";
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
