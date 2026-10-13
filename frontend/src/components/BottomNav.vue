<template>
  <nav class="nav glass-bar" aria-label="Horizon temporel">
    <div class="nav-inner" :style="{ '--active': activeIndex }">
      <span v-if="activeIndex >= 0" class="indicator" aria-hidden="true"><i /></span>
      <router-link
        v-for="tab in tabs"
        :key="tab.to"
        v-ripple
        :to="tab.to"
        class="item"
        :data-horizon="tab.horizon"
        @click="haptic()"
      >
        <span class="icon"><component :is="tab.icon" /></span>
        <span class="label">{{ tab.label }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, type Component } from "vue";
import { useRoute } from "vue-router";
import { History, Radar, Telescope } from "lucide-vue-next";
import { haptic } from "../lib/device";
import type { Horizon } from "../api";

const tabs: { to: string; label: string; horizon: Horizon; icon: Component }[] = [
  { to: "/past", label: "Passé", horizon: "past", icon: History },
  { to: "/now", label: "Maintenant", horizon: "now", icon: Radar },
  { to: "/future", label: "Futur", horizon: "future", icon: Telescope },
];

const route = useRoute();
const activeIndex = computed(() => (typeof route.meta.index === "number" ? route.meta.index : -1));
</script>

<style scoped>
.nav {
  position: fixed;
  inset: auto 0 0;
  z-index: 20;
  padding-bottom: var(--safe-b);
  view-transition-name: nav;
  background: var(--glass);
  border-top: 1px solid var(--line);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
}

.nav-inner {
  position: relative;
  max-width: var(--page-max);
  margin: 0 auto;
  height: var(--nav-h);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

/* One indicator that glides between tabs (translateX of a 1/3-wide track). */
.indicator {
  position: absolute;
  top: 12px;
  left: 0;
  width: calc(100% / 3);
  height: 34px;
  display: grid;
  place-items: center;
  pointer-events: none;
  transform: translateX(calc(var(--active) * 100%));
  transition: transform var(--dur-3) var(--ease-spring);
}

.indicator i {
  width: 64px;
  height: 34px;
  border-radius: 999px;
  background: rgb(var(--accent-rgb) / 0.2);
  border: 1px solid rgb(var(--accent-rgb) / 0.3);
  transition:
    background-color var(--dur-3) var(--ease-out),
    border-color var(--dur-3) var(--ease-out);
}

.item {
  position: relative;
  display: grid;
  justify-items: center;
  align-content: start;
  gap: 4px;
  padding-top: 12px;
  color: var(--muted);
  border-radius: var(--r-md);
  transition: color var(--dur-2) var(--ease-out);
}

.icon {
  display: grid;
  place-items: center;
  width: 64px;
  height: 34px;
}

.icon svg {
  width: 22px;
  height: 22px;
  transition: transform var(--dur-3) var(--ease-spring);
}

.label {
  font-size: 0.74rem;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.item.router-link-active {
  color: var(--ink);
}

.item.router-link-active .icon svg {
  color: var(--accent);
  transform: translateY(-1px) scale(1.08);
}

.item.router-link-active .label {
  font-weight: 800;
}

.item:active .icon svg {
  transform: scale(0.88);
}
</style>
