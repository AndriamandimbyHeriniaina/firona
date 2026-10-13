<template>
  <div class="app" :data-horizon="horizon">
    <div class="aura" aria-hidden="true">
      <i v-for="item in HORIZONS" :key="item" :data-horizon="item" :class="{ on: item === horizon }" />
    </div>

    <AppBar v-if="!isDetail" :busy="busy" @refresh="refresh" />

    <main class="main" :class="{ 'with-nav': !isDetail }">
      <router-view v-slot="{ Component, route: current }">
        <!-- View Transitions animate the swap natively; a CSS-less out-in <Transition>
             would finish its leave synchronously mid-patch and crash the RouterView. -->
        <component :is="Component" v-if="viewTransitions" :key="current.path" />
        <Transition v-else name="route" mode="out-in">
          <component :is="Component" :key="current.path" />
        </Transition>
      </router-view>
    </main>

    <BottomNav v-if="!isDetail" />
    <ToastHost :raised="!isDetail" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppBar from "./components/AppBar.vue";
import BottomNav from "./components/BottomNav.vue";
import ToastHost from "./components/ToastHost.vue";
import { HORIZONS, type Horizon } from "./api";
import { toast } from "./composables/useApp";
import { supportsViewTransitions } from "./lib/viewTransition";
import { useRadarStore } from "./stores/radar";

const route = useRoute();
const radar = useRadarStore();
const viewTransitions = supportsViewTransitions;

const isDetail = computed(() => Boolean(route.meta.depth));

// Article screens keep the accent of the horizon they were opened from.
const lastHorizon = ref<Horizon>("now");
watch(
  () => [route.meta.horizon, route.query.from] as const,
  ([metaHorizon, from]) => {
    if (metaHorizon) lastHorizon.value = metaHorizon;
    else if (typeof from === "string" && (HORIZONS as string[]).includes(from)) {
      lastHorizon.value = from as Horizon;
    }
  },
  { immediate: true },
);
const horizon = computed<Horizon>(() => route.meta.horizon ?? lastHorizon.value);

const busy = computed(() => {
  const slot = radar.horizons[horizon.value];
  return slot.refreshing || slot.status === "loading";
});

async function refresh() {
  try {
    await radar.loadHorizon(horizon.value, { force: true });
    toast("Radar à jour", "success", 1800);
  } catch {
    toast(radar.horizons[horizon.value].error || "Actualisation impossible", "error");
  }
}
</script>

<style scoped>
.app {
  position: relative;
  min-height: 100vh;
  min-height: 100dvh;
}

/* Horizon-tinted glow behind everything; layers crossfade (opacity only). */
.aura {
  position: fixed;
  inset: 0 0 auto;
  height: 70vh;
  z-index: -1;
  pointer-events: none;
}

.aura i {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 700ms var(--ease-out);
  background:
    radial-gradient(90% 55% at 15% -5%, rgb(var(--accent-rgb) / var(--aura-alpha)), transparent 70%),
    radial-gradient(70% 45% at 95% 5%, rgb(var(--green-rgb) / calc(var(--aura-alpha) * 0.6)), transparent 70%);
}

.aura i.on {
  opacity: 1;
}

.main {
  max-width: var(--page-max);
  margin: 0 auto;
  view-transition-name: page;
}

.main.with-nav {
  padding-bottom: calc(var(--nav-h) + var(--safe-b) + 24px);
}
</style>
