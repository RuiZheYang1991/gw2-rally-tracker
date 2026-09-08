<template>
  <span class="icon-slot" v-html="mark"></span>
</template>

<script setup>
import { computed } from "vue";
import { professionMark } from "../icons";

const props = defineProps({
  professionKey: { type: String, required: true },
  color: { type: String, default: "#e8c36a" },
  familyKey: { type: String, default: "" },
});

const mark = computed(() =>
  professionMark(props.professionKey, props.color, props.familyKey)
);
</script>
