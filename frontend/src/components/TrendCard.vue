<template>
  <router-link v-slot="{ href, navigate }" :to="to" custom>
    <a v-ripple :href="href" class="card surface" :data-label="item.label" @click="open($event, navigate)">
      <span class="thumb" :style="{ viewTransitionName: morph ? 'hero' : undefined }">
        <img
          v-if="item.product.image_url"
          :src="item.product.image_url"
          alt=""
          width="80"
          height="80"
          loading="lazy"
          decoding="async"
        />
        <span v-else class="initial">{{ item.product.name.charAt(0) }}</span>
      </span>

      <div class="body">
        <div class="top">
          <span class="rank num">{{ String(rank).padStart(2, "0") }}</span>
          <span class="cat">{{ item.product.category.name }}</span>
        </div>
        <h3 class="name">{{ item.product.name }}</h3>
        <div class="meta">
          <LabelPill :label="item.label" />
          <span class="momentum num" :data-sign="sign" :aria-label="`Élan ${momentumText}`">
            <component :is="momentumIcon" aria-hidden="true" />
            {{ momentumText }}
          </span>
        </div>
      </div>

      <ScoreRing
        class="score"
        :value="item.score"
        :caption="SCORE_TEXT[horizon]"
        :delay="delay"
        :animate="animate"
      />

      <TensionBar
        class="tension"
        compact
        :demand="item.demand_score"
        :supply="item.supply_score"
        :animate="animate"
      />
    </a>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-vue-next";
import LabelPill from "./LabelPill.vue";
import ScoreRing from "./ScoreRing.vue";
import TensionBar from "./TensionBar.vue";
import { SCORE_TEXT, type Horizon, type RadarItem } from "../api";
import { signedNumber } from "../lib/format";
import { useRadarStore } from "../stores/radar";

const props = withDefaults(
  defineProps<{ item: RadarItem; horizon: Horizon; rank: number; animate?: boolean }>(),
  { animate: true },
);

const radar = useRadarStore();
const to = computed(() => ({
  path: `/article/${props.item.product.slug}`,
  query: { from: props.horizon },
}));
const morph = computed(() => radar.activeSlug === props.item.product.slug);
const delay = computed(() => Math.min(props.rank - 1, 8) * 55);

const sign = computed(() => (props.item.momentum > 0 ? "up" : props.item.momentum < 0 ? "down" : "flat"));
const momentumText = computed(() => signedNumber(props.item.momentum));
const momentumIcon = computed(() =>
  sign.value === "up" ? ArrowUpRight : sign.value === "down" ? ArrowDownRight : ArrowRight,
);

function open(event: MouseEvent, navigate: (e?: MouseEvent) => unknown) {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  // Name this thumbnail before the router snapshots the page.
  radar.activeSlug = props.item.product.slug;
  navigate(event);
}
</script>

<style scoped>
.card {
  display: grid;
  grid-template-columns: 80px minmax(0, 1fr) auto;
  grid-template-areas:
    "thumb body score"
    "tension tension tension";
  align-items: center;
  column-gap: 0.85rem;
  row-gap: 0.85rem;
  padding: 12px 14px 14px 12px;
  transition:
    transform var(--dur-2) var(--ease-out),
    border-color var(--dur-2) var(--ease-out);
}

.card:active {
  transform: scale(0.982);
}

.thumb {
  grid-area: thumb;
  width: 80px;
  height: 80px;
  border-radius: var(--r-md);
  overflow: hidden;
  background: var(--surface-3);
  display: grid;
  place-items: center;
  contain: paint;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.initial {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--accent);
}

.body {
  grid-area: body;
  display: grid;
  gap: 4px;
  min-width: 0;
}

.top {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
}

.rank {
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--accent);
}

.cat {
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.name {
  font-size: 1.04rem;
  font-weight: 750;
  letter-spacing: -0.01em;
  line-height: 1.2;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 2px;
}

.momentum {
  display: inline-flex;
  align-items: center;
  gap: 1px;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--muted);
}

.momentum svg {
  width: 15px;
  height: 15px;
  stroke-width: 2.5;
}

.momentum[data-sign="up"] {
  color: var(--rising);
}

.momentum[data-sign="down"] {
  color: var(--falling);
}

.score {
  grid-area: score;
}

.tension {
  grid-area: tension;
  padding-top: 0.75rem;
  border-top: 1px dashed var(--line-2);
}
</style>
