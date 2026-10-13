<template>
  <section class="hero surface" aria-label="Vue radar">
    <div class="scope" :style="{ '--period': `${PERIOD}s` }">
      <svg class="grid" viewBox="0 0 200 200" aria-hidden="true">
        <circle cx="100" cy="100" r="97" />
        <circle cx="100" cy="100" r="66" />
        <circle cx="100" cy="100" r="35" />
        <line x1="100" y1="6" x2="100" y2="194" />
        <line x1="6" y1="100" x2="194" y2="100" />
      </svg>
      <div class="sweep" aria-hidden="true" />
      <span class="core" aria-hidden="true" />
      <router-link
        v-for="blip in blips"
        :key="blip.slug"
        :to="blip.to"
        class="blip"
        :class="{ leader: blip.leader, still: !animate }"
        :data-label="blip.label"
        :style="blip.style"
        :aria-label="`${blip.name}, score ${blip.score}`"
        @click="radar.activeSlug = null"
      >
        <i />
      </router-link>
    </div>

    <div class="side">
      <p class="eyebrow">En tête</p>
      <router-link v-if="leader" :to="leaderTo" class="leader" @click="radar.activeSlug = null">
        <strong class="leader-name">{{ leader.product.name }}</strong>
        <span class="leader-score num">{{ leaderScore }}<small>/100</small></span>
      </router-link>
      <ul class="legend">
        <li v-for="row in legend" :key="row.label" :data-label="row.label">
          <i aria-hidden="true" />
          <span>{{ LABEL_TEXT[row.label] }}</span>
          <b class="num">{{ row.count }}</b>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { LABEL_TEXT, type Horizon, type RadarItem, type TrendLabel } from "../api";
import { useCountUp } from "../composables/useCountUp";
import { useRadarStore } from "../stores/radar";

const props = withDefaults(
  defineProps<{ items: RadarItem[]; horizon: Horizon; animate?: boolean }>(),
  { animate: true },
);

/** Seconds per sweep; blips pulse when the beam crosses their bearing. */
const PERIOD = 4;
const MAX_BLIPS = 10;
const GOLDEN_ANGLE = 137.508;
const LABEL_ORDER: TrendLabel[] = ["rising", "emerging", "stable", "falling"];

const radar = useRadarStore();

const leader = computed(() => props.items[0] ?? null);
const leaderScore = useCountUp(() => leader.value?.score ?? 0, {
  delay: 200,
  instant: !props.animate,
});
const leaderTo = computed(() =>
  leader.value ? { path: `/article/${leader.value.product.slug}`, query: { from: props.horizon } } : "/",
);

const blips = computed(() =>
  props.items.slice(0, MAX_BLIPS).map((item, index) => {
    // Bearing is fixed per article (id), so blips only move in/out between horizons.
    const bearing = (item.product.id * GOLDEN_ANGLE) % 360;
    const radius = 0.16 + (1 - Math.max(0, Math.min(100, item.score)) / 100) * 0.74;
    const rad = (bearing * Math.PI) / 180;
    const x = 50 + Math.sin(rad) * radius * 50;
    const y = 50 - Math.cos(rad) * radius * 50;
    return {
      slug: item.product.slug,
      name: item.product.name,
      score: item.score,
      label: item.label,
      leader: index === 0,
      to: { path: `/article/${item.product.slug}`, query: { from: props.horizon } },
      style: {
        left: `${x}%`,
        top: `${y}%`,
        "--delay": `${(bearing / 360) * PERIOD - PERIOD}s`,
        "--i": index,
        viewTransitionName: `blip-${item.product.slug}`,
      },
    };
  }),
);

const legend = computed(() =>
  LABEL_ORDER.map((label) => ({
    label,
    count: props.items.filter((item) => item.label === label).length,
  })).filter((row) => row.count > 0),
);
</script>

<style scoped>
.hero {
  display: grid;
  grid-template-columns: minmax(0, 11.5rem) minmax(0, 1fr);
  align-items: center;
  gap: 1rem;
  padding: 14px 16px 14px 14px;
  overflow: hidden;
}

.scope {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 50%;
  view-transition-name: scope;
  background: radial-gradient(circle, rgb(var(--accent-rgb) / 0.09), transparent 70%);
  contain: layout paint;
}

.grid {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  fill: none;
  stroke: rgb(var(--ink-rgb) / 0.11);
  stroke-width: 1;
}

.grid circle:first-child {
  stroke: rgb(var(--accent-rgb) / 0.35);
}

.sweep {
  position: absolute;
  inset: 1.5%;
  border-radius: 50%;
  background: conic-gradient(
    from 0deg,
    transparent 0deg 250deg,
    rgb(var(--accent-rgb) / 0.05) 290deg,
    rgb(var(--accent-rgb) / 0.42) 359.5deg,
    transparent 360deg
  );
  animation: spin var(--period) linear infinite;
  will-change: transform;
}

.sweep::after {
  content: "";
  position: absolute;
  left: calc(50% - 1px);
  top: 0;
  width: 2px;
  height: 50%;
  border-radius: 2px;
  background: linear-gradient(to top, transparent, var(--accent));
}

.core {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 10px;
  height: 10px;
  margin: -5px 0 0 -5px;
  border-radius: 50%;
  background: var(--ink);
  box-shadow: 0 0 0 4px rgb(var(--ink-rgb) / 0.12);
}

/* 36px touch target around a small dot. */
.blip {
  position: absolute;
  width: 36px;
  height: 36px;
  margin: -18px 0 0 -18px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  animation: fade-in var(--dur-4) var(--ease-out) both;
  animation-delay: calc(var(--i) * 70ms + 200ms);
}

.blip.still {
  animation: none;
}

.blip i {
  position: relative;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--tone);
  box-shadow: 0 0 10px rgb(var(--tone-rgb) / 0.7);
}

.blip.leader i {
  width: 13px;
  height: 13px;
  outline: 2px solid rgb(var(--tone-rgb) / 0.4);
  outline-offset: 3px;
}

.blip i::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--tone);
  opacity: 0;
  animation: ping var(--period) var(--ease-out) infinite;
  animation-delay: var(--delay);
}

@keyframes ping {
  0% {
    transform: scale(1);
    opacity: 0.85;
  }
  32%,
  100% {
    transform: scale(3.4);
    opacity: 0;
  }
}

.blip:active i {
  transform: scale(1.3);
}

.side {
  display: grid;
  gap: 0.55rem;
  min-width: 0;
}

.leader {
  display: grid;
  gap: 2px;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--line);
}

.leader-name {
  font-size: 1.02rem;
  font-weight: 750;
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.leader-score {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1;
  color: var(--accent);
}

.leader-score small {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--muted);
  margin-left: 2px;
}

.legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.3rem;
}

.legend li {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.78rem;
  color: var(--ink-2);
}

.legend i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--tone);
}

.legend b {
  font-weight: 800;
  color: var(--ink);
}

@media (max-width: 359px) {
  .hero {
    grid-template-columns: 1fr;
    justify-items: center;
  }
  .scope {
    max-width: 13rem;
  }
  .side {
    width: 100%;
  }
}
</style>
