<template>
  <div class="state rise" role="status">
    <span class="glyph" :data-tone="tone">
      <component :is="icon" aria-hidden="true" />
    </span>
    <h3>{{ title }}</h3>
    <p>{{ text }}</p>
    <button v-if="action" v-ripple type="button" class="btn" @click="$emit('action')">
      <RefreshCw aria-hidden="true" />
      {{ action }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { CircleAlert, RefreshCw, SearchX, WifiOff } from "lucide-vue-next";

const props = defineProps<{
  tone: "error" | "empty" | "offline";
  title: string;
  text: string;
  action?: string;
}>();
defineEmits<{ action: [] }>();

const icon = computed(() =>
  props.tone === "offline" ? WifiOff : props.tone === "error" ? CircleAlert : SearchX,
);
</script>

<style scoped>
.state {
  display: grid;
  justify-items: center;
  gap: 0.55rem;
  padding: 2.5rem 1.25rem;
  text-align: center;
}

.glyph {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  margin-bottom: 0.4rem;
  border-radius: 22px;
  color: var(--accent);
  background: rgb(var(--accent-rgb) / 0.14);
}

.glyph[data-tone="error"],
.glyph[data-tone="offline"] {
  color: var(--falling);
  background: rgb(var(--falling-rgb) / 0.14);
}

.glyph svg {
  width: 28px;
  height: 28px;
}

h3 {
  font-size: 1.1rem;
  font-weight: 750;
}

p {
  max-width: 22rem;
  color: var(--muted);
  font-size: 0.92rem;
}

.btn {
  margin-top: 0.8rem;
}
</style>
