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
      <span v-if="selected" class="role-select-slot">
        <img
          class="role-select-icon"
          :class="'role-select-icon--' + selected.key"
          :src="roleIcon(selected.key)"
          :alt="selected.name_en"
        />
      </span>
      <span>{{ selected ? displayName(selected) : "" }}</span>
    </button>
    <ul v-if="open" class="prof-select-list" role="listbox">
      <li v-for="r in options" :key="r.key">
        <button
          type="button"
          class="prof-select-option notranslate"
          :class="{ active: r.key === modelValue }"
          role="option"
          :aria-selected="r.key === modelValue"
          @click="choose(r.key)"
        >
          <span class="role-select-slot">
            <img
              class="role-select-icon"
              :class="'role-select-icon--' + r.key"
              :src="roleIcon(r.key)"
              :alt="r.name_en"
            />
          </span>
          <span>{{ displayName(r) }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { displayName } from "../i18n";
import { roleIcon } from "../roleIcons";

const props = defineProps({
  modelValue: { type: String, default: "" },
  options: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);
const open = ref(false);
const host = ref(null);

const selected = computed(
  () => props.options.find((r) => r.key === props.modelValue) || props.options[0] || null
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
