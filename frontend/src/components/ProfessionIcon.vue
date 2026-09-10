<template>
  <span class="icon-slot">
    <img
      v-if="!failed"
      class="prof-img"
      :src="src"
      :alt="professionKey"
      :width="size"
      :height="size"
      :style="sizeStyle"
      loading="eager"
      decoding="async"
      @error="failed = true"
    />
    <span v-else class="prof-mark" :style="sizeStyle" v-html="mark"></span>
  </span>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { professionMark } from "../icons";

const props = defineProps({
  professionKey: { type: String, required: true },
  color: { type: String, default: "#e8c36a" },
  familyKey: { type: String, default: "" },
  size: { type: Number, default: 48 },
});

const failed = ref(false);
const src = computed(() => `/img/professions/${props.professionKey}.png`);
const mark = computed(() =>
  professionMark(props.professionKey, props.color, props.familyKey)
);
const sizeStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
}));

watch(
  () => props.professionKey,
  () => {
    failed.value = false;
  }
);
</script>

<style scoped>
.prof-img,
.prof-mark :deep(svg) {
  object-fit: contain;
  display: block;
}

.prof-mark {
  display: inline-flex;
}

.prof-mark :deep(svg) {
  width: 100%;
  height: 100%;
}
</style>
