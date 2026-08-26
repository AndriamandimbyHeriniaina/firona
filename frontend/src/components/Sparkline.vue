<template>
  <svg class="spark" viewBox="0 0 120 36" role="img" :aria-label="label">
    <polyline fill="none" stroke="currentColor" stroke-width="2.5" :points="points" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ values: number[]; label: string }>();

const points = computed(() => {
  const vals = props.values.length ? props.values : [0];
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = Math.max(max - min, 1);
  return vals
    .map((value, index) => {
      const x = vals.length === 1 ? 60 : (index / (vals.length - 1)) * 120;
      const y = 32 - ((value - min) / span) * 28;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
});
</script>
