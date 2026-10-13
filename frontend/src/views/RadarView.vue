<template>
  <section ref="pageEl" class="page" :data-horizon="horizon">
    <PullIndicator :distance="gesture.pull" :refreshing="gesture.refreshing" :dragging="gesture.dragging" />

    <div class="slide" :class="{ dragging: gesture.dragging }" :style="{ '--dx': `${gesture.dx}px` }">
      <header class="head">
        <p class="kicker">
          <component :is="copy.icon" aria-hidden="true" />
          {{ copy.kicker }}
        </p>
        <h2 class="title">{{ HORIZON_TEXT[horizon] }}</h2>
        <p class="sub">{{ copy.sub }}</p>
        <p v-if="updatedAt" class="fresh">
          <span class="live-dot" :class="freshness" />
          Mis à jour {{ timeAgo(updatedAt, now) }}
          <span v-if="slot.refreshing" class="syncing">· synchronisation…</span>
        </p>
      </header>

      <div v-if="slot.status === 'loading' || slot.status === 'idle'" class="stack" aria-busy="true">
        <div class="skeleton hero-sk" />
        <SkeletonCard v-for="n in 3" :key="n" />
        <span class="sr-only">Lecture du radar…</span>
      </div>

      <StateBlock
        v-else-if="slot.status === 'error'"
        :tone="online ? 'error' : 'offline'"
        :title="online ? 'Le radar ne répond pas' : 'Vous êtes hors ligne'"
        :text="slot.error"
        action="Réessayer"
        @action="reload"
      />

      <StateBlock
        v-else-if="!items.length"
        tone="empty"
        title="Rien sur le radar"
        text="Aucun article n’a encore de score pour cet horizon. Revenez après la prochaine collecte."
        action="Actualiser"
        @action="reload"
      />

      <div v-else class="stack">
        <RadarScope :items="items" :horizon="horizon" :animate="animateIn" :class="{ rise: animateIn }" />

        <div class="section-head" :class="{ rise: animateIn }" style="--i: 1">
          <h3>Classement</h3>
          <span class="count">{{ items.length }} article{{ items.length > 1 ? "s" : "" }}</span>
        </div>

        <ol class="cards">
          <li
            v-for="(item, index) in items"
            :key="item.product.id"
            :class="{ rise: animateIn }"
            :style="{ '--i': index + 2 }"
          >
            <TrendCard :item="item" :horizon="horizon" :rank="index + 1" :animate="animateIn" />
          </li>
        </ol>

        <Transition name="hint">
          <p v-if="showHint" class="hint">
            <MoveHorizontal aria-hidden="true" />
            Glissez pour changer d’horizon · tirez vers le bas pour actualiser
          </p>
        </Transition>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { History, MoveHorizontal, Radar, Telescope } from "lucide-vue-next";
import PullIndicator from "../components/PullIndicator.vue";
import RadarScope from "../components/RadarScope.vue";
import SkeletonCard from "../components/SkeletonCard.vue";
import StateBlock from "../components/StateBlock.vue";
import TrendCard from "../components/TrendCard.vue";
import { HORIZON_TEXT, HORIZONS, type Horizon } from "../api";
import { toast, useOnline } from "../composables/useApp";
import { useTouchGestures } from "../composables/useTouchGestures";
import { latestIso, timeAgo } from "../lib/format";
import { useRadarStore } from "../stores/radar";

const props = defineProps<{ horizon: Horizon }>();

const COPY = {
  past: {
    icon: History,
    kicker: "Mémoire du marché",
    sub: "Ce qui se cherchait d’habitude à cette période de l’année.",
  },
  now: {
    icon: Radar,
    kicker: "En direct",
    sub: "Les articles les plus cherchés en ce moment à Madagascar.",
  },
  future: {
    icon: Telescope,
    kicker: "Signaux faibles",
    sub: "Ce qui pourrait monter dans les semaines qui viennent.",
  },
} as const;

const HINT_KEY = "firona:gesture-hint";
const STALE_MS = 13 * 3600 * 1000;

const radar = useRadarStore();
const router = useRouter();
const online = useOnline();
const pageEl = ref<HTMLElement | null>(null);

const slot = computed(() => radar.horizons[props.horizon]);
const items = computed(() => slot.value.data);
const copy = computed(() => COPY[props.horizon]);
// Stagger only when rows arrive after mount; cached rows must stay still for view transitions.
const animateIn = ref(slot.value.status !== "ready");

const now = ref(Date.now());
const clock = window.setInterval(() => (now.value = Date.now()), 30_000);
onBeforeUnmount(() => window.clearInterval(clock));

const updatedAt = computed(() => latestIso(items.value.map((item) => item.captured_at)));
const freshness = computed(() => {
  if (!online.value) return "off";
  if (!updatedAt.value) return "off";
  return now.value - new Date(updatedAt.value).getTime() > STALE_MS ? "stale" : "";
});

const showHint = ref(readHint());
function readHint(): boolean {
  try {
    return window.localStorage.getItem(HINT_KEY) !== "done";
  } catch {
    return false;
  }
}
function dismissHint() {
  showHint.value = false;
  try {
    window.localStorage.setItem(HINT_KEY, "done");
  } catch {
    // Private mode: the hint simply comes back next time.
  }
}

const index = computed(() => HORIZONS.indexOf(props.horizon));
function neighbour(direction: "left" | "right"): Horizon | undefined {
  return HORIZONS[index.value + (direction === "left" ? 1 : -1)];
}

async function reload() {
  try {
    await radar.loadHorizon(props.horizon, { force: true });
  } catch {
    toast(slot.value.error || "Actualisation impossible", "error");
  }
}

const gesture = useTouchGestures(pageEl, {
  canSwipe: (direction) => Boolean(neighbour(direction)),
  onSwipe: (direction) => {
    const target = neighbour(direction);
    if (!target) return false;
    dismissHint();
    router.push(`/${target}`);
  },
  onRefresh: async () => {
    dismissHint();
    try {
      await radar.loadHorizon(props.horizon, { force: true });
      toast("Radar à jour", "success", 1600);
    } catch {
      toast(slot.value.error || "Actualisation impossible", "error");
    }
  },
});

function load() {
  radar
    .loadHorizon(props.horizon)
    .then(() => radar.prefetchHorizons(props.horizon))
    .catch(() => undefined);
}

onMounted(load);
watch(() => props.horizon, load);
</script>

<style scoped>
.page {
  position: relative;
  min-height: calc(100vh - var(--bar-h) - var(--nav-h));
  min-height: calc(100dvh - var(--bar-h) - var(--nav-h));
  padding: 4px var(--gutter) 0;
  /* Vertical scroll stays native; horizontal moves feed the swipe gesture. */
  touch-action: pan-y;
}

.slide {
  transform: translateX(var(--dx));
  transition: transform var(--dur-3) var(--ease-spring);
}

.slide.dragging {
  transition: none;
}

.head {
  padding: 10px 2px 18px;
  animation: fade-in var(--dur-3) var(--ease-out) both;
}

.kicker {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
}

.kicker svg {
  width: 15px;
  height: 15px;
  stroke-width: 2.4;
}

.title {
  margin-top: 4px;
  font-size: clamp(2rem, 9vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 1.05;
}

.sub {
  margin-top: 6px;
  max-width: 26rem;
  color: var(--ink-2);
  font-size: 0.95rem;
}

.fresh {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 12px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
}

.syncing {
  color: var(--accent);
}

.stack {
  display: grid;
  gap: 14px;
}

.hero-sk {
  height: 13.5rem;
  border-radius: var(--r-lg);
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 10px 2px 0;
}

.section-head h3 {
  font-size: 1.08rem;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.count {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
}

.cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 12px;
}

.hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.6rem 0 0.2rem;
  font-size: 0.78rem;
  color: var(--muted);
  text-align: center;
}

.hint svg {
  width: 16px;
  height: 16px;
  flex: none;
}

.hint-leave-active {
  transition: opacity var(--dur-3) var(--ease-out);
}

.hint-leave-to {
  opacity: 0;
}
</style>
