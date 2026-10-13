<template>
  <div
    v-reveal
    class="ring"
    :class="[size, { 'is-in': !animate, still: !animate }]"
    :style="{ '--p': clamped / 100, '--delay': `${delay}ms` }"
    role="img"
    :aria-label="`${caption} ${value ?? 'inconnu'} sur 100`"
  >
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <circle class="track" cx="32" cy="32" r="27" />
      <circle class="value" cx="32" cy="32" r="27" pathLength="100" />
    </svg>
    <span class="center">
      <strong class="num">{{ value === null ? "—" : shown }}</strong>
      <small v-if="size === 'lg'">{{ caption }}</small>
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useCountUp } from "../composables/useCountUp";

const props = withDefaults(
  defineProps<{
    value: number | null;
    caption: string;
    size?: "sm" | "lg";
    delay?: number;
    /** false = render at the final value (cached screens, back navigation). */
    animate?: boolean;
  }>(),
  { size: "sm", delay: 0, animate: true },
);

const clamped = computed(() => Math.max(0, Math.min(100, props.value ?? 0)));
const shown = useCountUp(() => clamped.value, {
  delay: props.delay + 150,
  instant: !props.animate,
});
</script>

<style scoped>
.ring {
  position: relative;
  width: 58px;
  height: 58px;
  flex: none;
}

.ring.lg {
  width: 92px;
  height: 92px;
}

svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

circle {
  fill: none;
  stroke-width: 6;
  stroke-linecap: round;
}

.lg circle {
  stroke-width: 5;
}

.track {
  stroke: rgb(var(--ink-rgb) / 0.09);
}

.value {
  stroke: var(--accent);
  stroke-dasharray: 100 100;
  stroke-dashoffset: 100;
  transition: stroke-dashoffset 1100ms var(--ease-out) var(--delay);
}

.still .value {
  transition: none;
}

.ring.is-in .value {
  stroke-dashoffset: calc(100 - var(--p) * 100);
}

.center {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
  line-height: 1;
}

strong {
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.lg strong {
  font-size: 1.55rem;
}

small {
  margin-top: 4px;
  font-size: 0.54rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
}
</style>
