<template>
  <div ref="host" class="prof-select" :class="{ open, disabled }">
    <button
      type="button"
      class="prof-select-btn notranslate"
      :disabled="disabled"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
    >
      <span v-if="selected" class="prof-select-icon-slot">
        <ProfessionIcon
          :profession-key="selected.key"
          :family-key="selected.family_key"
          :color="selected.color"
          :size="professionIconSize(selected, 28)"
        />
      </span>
      <span>{{ selected ? displayName(selected) : "" }}</span>
    </button>
    <ul v-if="open" class="prof-select-list" role="listbox">
      <li v-for="p in options" :key="p.key">
        <button
          type="button"
          class="prof-select-option notranslate"
          :class="{ active: p.key === modelValue }"
          role="option"
          :aria-selected="p.key === modelValue"
          @click="choose(p.key)"
        >
          <span class="prof-select-icon-slot">
            <ProfessionIcon
              :profession-key="p.key"
              :family-key="p.family_key"
              :color="p.color"
              :size="professionIconSize(p, 26)"
            />
          </span>
          <span>{{ displayName(p) }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import ProfessionIcon from "./ProfessionIcon.vue";
import { displayName } from "../i18n";
import { professionIconSize } from "../professions";

const props = defineProps({
  modelValue: { type: String, default: "" },
  options: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);
const open = ref(false);
const host = ref(null);

const selected = computed(
  () => props.options.find((p) => p.key === props.modelValue) || props.options[0] || null
);

function toggle() {
  if (props.disabled) return;
  open.value = !open.value;
}

function choose(key) {
  emit("update:modelValue", key);
  open.value = false;
}

function onDocClick(ev) {
  if (!open.value) return;
  if (!host.value?.contains(ev.target)) open.value = false;
}

function onKey(ev) {
  if (ev.key === "Escape") open.value = false;
}

onMounted(() => {
  document.addEventListener("click", onDocClick);
  document.addEventListener("keydown", onKey);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", onDocClick);
  document.removeEventListener("keydown", onKey);
});
</script>
