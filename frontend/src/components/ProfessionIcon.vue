<template>
  <span class="icon-slot">
    <img
      v-if="!failed"
      class="prof-img"
      :src="src"
      :alt="professionKey"
      @error="failed = true"
    />
    <span v-else v-html="mark"></span>
  </span>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { professionMark } from "../icons";

const props = defineProps({
  professionKey: { type: String, required: true },
  color: { type: String, default: "#e8c36a" },
  familyKey: { type: String, default: "" },
});

const failed = ref(false);
const src = computed(() => `/img/professions/${props.professionKey}.png`);
const mark = computed(() =>
  professionMark(props.professionKey, props.color, props.familyKey)
);

watch(
  () => props.professionKey,
  () => {
    failed.value = false;
  }
);
</script>

<style scoped>
.prof-img {
  width: 48px;
  height: 48px;
  object-fit: contain;
  display: block;
}
</style>
