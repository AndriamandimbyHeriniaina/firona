<template>
  <span class="pill" :data-label="label">
    <component :is="icon" aria-hidden="true" />
    {{ LABEL_TEXT[label] }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Minus, Sparkles, TrendingDown, TrendingUp } from "lucide-vue-next";
import { LABEL_TEXT, type TrendLabel } from "../api";

const props = defineProps<{ label: TrendLabel }>();

const ICONS = {
  rising: TrendingUp,
  falling: TrendingDown,
  stable: Minus,
  emerging: Sparkles,
} as const;

const icon = computed(() => ICONS[props.label]);
</script>
