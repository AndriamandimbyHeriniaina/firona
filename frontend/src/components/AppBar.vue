<template>
  <header class="appbar glass-bar">
    <div class="appbar-inner">
      <router-link to="/now" class="brand-link" aria-label="Firona, accueil">
        <BrandMark />
        <span class="titles">
          <span class="eyebrow">Marché malgache</span>
          <span class="title">Firona</span>
        </span>
      </router-link>
      <div class="actions">
        <button
          v-if="canInstall"
          v-ripple
          type="button"
          class="icon-btn install"
          aria-label="Installer l’application"
          @click="onInstall"
        >
          <Download />
        </button>
        <button
          v-ripple
          type="button"
          class="icon-btn"
          :class="{ spinning: busy }"
          :disabled="busy"
          aria-label="Actualiser le radar"
          @click="$emit('refresh')"
        >
          <RefreshCw />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Download, RefreshCw } from "lucide-vue-next";
import BrandMark from "./BrandMark.vue";
import { useInstallPrompt } from "../composables/useApp";

defineProps<{ busy: boolean }>();
defineEmits<{ refresh: [] }>();

const { canInstall, install } = useInstallPrompt();

function onInstall() {
  install().catch(() => undefined);
}
</script>

<style scoped>
.appbar {
  position: sticky;
  top: 0;
  z-index: 20;
  padding-top: var(--safe-t);
  view-transition-name: appbar;
  border-bottom: 1px solid transparent;
  background: rgb(var(--bg-rgb) / 0.55);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
}

/* Solidify the bar once content scrolls under it (compositor-driven). */
@supports (animation-timeline: scroll()) {
  .appbar {
    animation: bar-solid linear both;
    animation-timeline: scroll(root);
    animation-range: 0 64px;
  }
}

@keyframes bar-solid {
  from {
    background: transparent;
    border-bottom-color: transparent;
    backdrop-filter: none;
  }
  to {
    background: var(--glass);
    border-bottom-color: var(--line);
  }
}

.appbar-inner {
  max-width: var(--page-max);
  margin: 0 auto;
  height: var(--bar-h);
  padding: 0 calc(var(--gutter) - 4px) 0 var(--gutter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-height: 44px;
}

.titles {
  display: grid;
  line-height: 1.1;
}

.titles .eyebrow {
  font-size: 0.62rem;
  color: var(--gold);
}

.title {
  font-size: 1.28rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.actions {
  display: flex;
  gap: 0.15rem;
}

.icon-btn.install {
  color: var(--accent);
}

.spinning svg {
  animation: spin 0.9s linear infinite;
}
</style>
