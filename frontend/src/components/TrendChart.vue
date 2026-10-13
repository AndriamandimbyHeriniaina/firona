<template>
  <figure v-reveal class="chart">
    <div ref="plotEl" class="plot" @pointerdown="scrub" @pointermove="scrub" @pointerleave="active = null">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="summary">
        <defs>
          <linearGradient :id="`${uid}-area`" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="var(--green)" stop-opacity="0.32" />
            <stop offset="1" stop-color="var(--green)" stop-opacity="0" />
          </linearGradient>
        </defs>
        <g class="grid">
          <line v-for="tick in ticks" :key="tick" :x1="0" :x2="W" :y1="y(tick)" :y2="y(tick)" />
        </g>
        <path class="area" :d="demandArea" :fill="`url(#${uid}-area)`" />
        <path class="line supply" :d="supplyLine" pathLength="1" />
        <path class="line demand" :d="demandLine" pathLength="1" />
        <g v-if="active !== null" class="cursor">
          <line :x1="x(active)" :x2="x(active)" y1="0" :y2="H" />
          <circle class="dot demand" :cx="x(active)" :cy="y(points[active].demand_score)" r="4.5" />
          <circle class="dot supply" :cx="x(active)" :cy="y(points[active].supply_score)" r="4" />
        </g>
        <circle
          v-else-if="points.length"
          class="dot demand last"
          :cx="x(points.length - 1)"
          :cy="y(points[points.length - 1].demand_score)"
          r="4.5"
        />
      </svg>
      <span v-for="tick in ticks" :key="`t${tick}`" class="tick num" :style="{ top: `${y(tick)}px` }">
        {{ tick }}
      </span>
      <div v-if="active !== null" class="tip" :style="{ left: `${x(active)}px` }" :data-edge="edge">
        <b>{{ formatShortDay(points[active].captured_at) }}</b>
        <span><i class="key demand" />Demande <strong class="num">{{ points[active].demand_score }}</strong></span>
        <span><i class="key supply" />Offre <strong class="num">{{ points[active].supply_score }}</strong></span>
      </div>
    </div>
    <figcaption class="axis">
      <span>{{ points.length ? formatDayMonth(points[0].captured_at) : "" }}</span>
      <span class="legend">
        <span><i class="key demand" />Demande</span>
        <span><i class="key supply dashed" />Offre</span>
      </span>
      <span>{{ points.length ? formatDayMonth(points[points.length - 1].captured_at) : "" }}</span>
    </figcaption>
  </figure>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import type { HistoryPoint } from "../api";
import { formatDayMonth, formatShortDay } from "../lib/format";

const props = defineProps<{ points: HistoryPoint[] }>();

const H = 160;
const PAD_Y = 12;
const uid = `chart-${Math.random().toString(36).slice(2, 8)}`;

// Real pixel width keeps dots round and dashes even (no non-uniform SVG scaling).
const W = ref(320);
const plotEl = ref<HTMLElement | null>(null);
let observer: ResizeObserver | null = null;
onMounted(() => {
  if (!plotEl.value) return;
  W.value = plotEl.value.clientWidth || 320;
  observer = new ResizeObserver(([entry]) => {
    W.value = Math.max(120, Math.round(entry.contentRect.width));
  });
  observer.observe(plotEl.value);
});
onBeforeUnmount(() => observer?.disconnect());

const active = ref<number | null>(null);

const domain = computed(() => {
  const values = props.points.flatMap((p) => [p.demand_score, p.supply_score]);
  if (!values.length) return [0, 100] as const;
  const lo = Math.max(0, Math.floor((Math.min(...values) - 8) / 10) * 10);
  const hi = Math.min(100, Math.ceil((Math.max(...values) + 8) / 10) * 10);
  return [lo, Math.max(hi, lo + 20)] as const;
});

const ticks = computed(() => {
  const [lo, hi] = domain.value;
  return [hi, Math.round((lo + hi) / 2), lo];
});

function x(index: number): number {
  const n = props.points.length;
  return n <= 1 ? W.value / 2 : (index / (n - 1)) * W.value;
}

function y(value: number): number {
  const [lo, hi] = domain.value;
  return PAD_Y + (1 - (value - lo) / (hi - lo)) * (H - PAD_Y * 2);
}

/** Monotone cubic (Fritsch–Carlson): smooth without overshooting the data. */
function smooth(values: number[]): string {
  const pts = values.map((v, i) => [x(i), y(v)] as const);
  if (!pts.length) return "";
  if (pts.length === 1) return `M0,${pts[0][1]} L${W.value},${pts[0][1]}`;
  const n = pts.length;
  const dx: number[] = [];
  const slope: number[] = [];
  for (let i = 0; i < n - 1; i += 1) {
    dx.push(pts[i + 1][0] - pts[i][0]);
    slope.push((pts[i + 1][1] - pts[i][1]) / dx[i]);
  }
  const tangent: number[] = [slope[0]];
  for (let i = 1; i < n - 1; i += 1) {
    tangent.push(slope[i - 1] * slope[i] <= 0 ? 0 : (slope[i - 1] + slope[i]) / 2);
  }
  tangent.push(slope[n - 2]);
  for (let i = 0; i < n - 1; i += 1) {
    if (slope[i] === 0) {
      tangent[i] = 0;
      tangent[i + 1] = 0;
      continue;
    }
    const a = tangent[i] / slope[i];
    const b = tangent[i + 1] / slope[i];
    const h = a * a + b * b;
    if (h > 9) {
      const t = 3 / Math.sqrt(h);
      tangent[i] = t * a * slope[i];
      tangent[i + 1] = t * b * slope[i];
    }
  }
  let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
  for (let i = 0; i < n - 1; i += 1) {
    const c1x = pts[i][0] + dx[i] / 3;
    const c1y = pts[i][1] + (tangent[i] * dx[i]) / 3;
    const c2x = pts[i + 1][0] - dx[i] / 3;
    const c2y = pts[i + 1][1] - (tangent[i + 1] * dx[i]) / 3;
    d += ` C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${pts[i + 1][0].toFixed(1)},${pts[i + 1][1].toFixed(1)}`;
  }
  return d;
}

const demandLine = computed(() => smooth(props.points.map((p) => p.demand_score)));
const supplyLine = computed(() => smooth(props.points.map((p) => p.supply_score)));
const demandArea = computed(() =>
  demandLine.value ? `${demandLine.value} L${W.value},${H} L0,${H} Z` : "",
);

const edge = computed(() => {
  if (active.value === null) return "";
  const ratio = x(active.value) / W.value;
  return ratio < 0.2 ? "start" : ratio > 0.8 ? "end" : "";
});

const summary = computed(() => {
  const pts = props.points;
  if (!pts.length) return "Pas d’historique";
  const first = pts[0].demand_score;
  const last = pts[pts.length - 1].demand_score;
  return `Demande de ${first} à ${last} sur ${pts.length} jours`;
});

function scrub(event: PointerEvent) {
  const n = props.points.length;
  if (!n) return;
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
  active.value = Math.round(ratio * (n - 1));
}
</script>

<style scoped>
.chart {
  margin: 0;
}

.plot {
  position: relative;
  height: 160px;
  /* Horizontal drags scrub the chart; vertical drags still scroll the page. */
  touch-action: pan-y;
  user-select: none;
}

svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.grid line {
  stroke: var(--line-2);
  stroke-dasharray: 2 4;
}

.tick {
  position: absolute;
  right: 0;
  transform: translateY(-120%);
  font-size: 0.66rem;
  font-weight: 600;
  color: var(--muted);
  pointer-events: none;
}

.line {
  fill: none;
  stroke-width: 2.6;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 1 1;
  stroke-dashoffset: 1;
  transition: stroke-dashoffset 1400ms var(--ease-out);
}

.line.demand {
  stroke: var(--green);
}

.line.supply {
  stroke: var(--gold);
  stroke-width: 2;
  opacity: 0.9;
  transition-delay: 200ms;
}

.area {
  opacity: 0;
  transition: opacity 900ms var(--ease-out) 500ms;
}

.is-in .line {
  stroke-dashoffset: 0;
}

/* The dash trick draws the line in; once drawn, show the supply dashes. */
.is-in .line.supply {
  animation: supply-dash 0s linear 1700ms forwards;
}

@keyframes supply-dash {
  to {
    stroke-dasharray: 0.012 0.012;
  }
}

.is-in .area {
  opacity: 1;
}

.cursor line {
  stroke: var(--ink-2);
  stroke-width: 1;
}

.dot {
  stroke: var(--surface);
  stroke-width: 2;
}

.dot.demand {
  fill: var(--green);
}

.dot.supply {
  fill: var(--gold);
}

.dot.last {
  opacity: 0;
  transition: opacity var(--dur-3) var(--ease-out) 1300ms;
}

.is-in .dot.last {
  opacity: 1;
}

.tip {
  position: absolute;
  top: -6px;
  transform: translate(-50%, -100%);
  display: grid;
  gap: 2px;
  min-width: 8.5rem;
  padding: 0.5rem 0.7rem;
  border-radius: 12px;
  font-size: 0.74rem;
  color: var(--ink-2);
  background: var(--surface-3);
  border: 1px solid var(--line-2);
  box-shadow: var(--shadow-2);
  pointer-events: none;
}

.tip[data-edge="start"] {
  transform: translate(-12%, -100%);
}

.tip[data-edge="end"] {
  transform: translate(-88%, -100%);
}

.tip b {
  font-size: 0.76rem;
  color: var(--ink);
  text-transform: capitalize;
}

.tip span {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.tip strong {
  margin-left: auto;
  color: var(--ink);
}

.key {
  display: inline-block;
  width: 10px;
  height: 3px;
  border-radius: 2px;
}

.key.demand {
  background: var(--green);
}

.key.supply {
  background: var(--gold);
}

.key.dashed {
  background: repeating-linear-gradient(90deg, var(--gold) 0 3px, transparent 3px 5px);
}

.axis {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--muted);
}

.legend {
  display: flex;
  gap: 0.8rem;
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
</style>
