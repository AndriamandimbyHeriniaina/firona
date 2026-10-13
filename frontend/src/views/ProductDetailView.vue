<template>
  <article class="detail" :data-horizon="from">
    <header class="topbar">
      <button v-ripple type="button" class="icon-btn glass" aria-label="Retour au radar" @click="goBack">
        <ArrowLeft />
      </button>
      <p class="topbar-title" aria-hidden="true">{{ product?.name }}</p>
      <button
        v-if="product"
        v-ripple
        type="button"
        class="icon-btn glass"
        aria-label="Partager cet article"
        @click="share"
      >
        <Share2 />
      </button>
    </header>

    <StateBlock
      v-if="!product && slot?.status === 'error'"
      class="missing"
      :tone="slot.error.includes('connexion') ? 'offline' : 'error'"
      title="Article indisponible"
      :text="slot.error"
      action="Réessayer"
      @action="reload"
    />

    <template v-else>
      <div class="hero">
        <div v-if="product" ref="carouselEl" class="carousel" @scroll.passive="onCarousel">
          <img
            v-for="(src, index) in gallery"
            :key="src"
            :src="src"
            :alt="index === 0 ? product.name : `${product.name}, image ${index + 1}`"
            width="640"
            height="400"
            :loading="index === 0 ? 'eager' : 'lazy'"
            decoding="async"
          />
          <span v-if="!gallery.length" class="placeholder">{{ product.name.charAt(0) }}</span>
        </div>
        <div v-else class="carousel skeleton" />
        <div class="shade" aria-hidden="true" />
        <div v-if="gallery.length > 1" class="dots">
          <button
            v-for="(src, index) in gallery"
            :key="src"
            type="button"
            :class="{ on: index === slide }"
            :aria-label="`Image ${index + 1} sur ${gallery.length}`"
            @click="goTo(index)"
          />
        </div>
      </div>

      <div class="sheet">
        <div class="head">
          <template v-if="product">
            <p class="eyebrow">{{ product.category.name }}</p>
            <h1 class="name">{{ product.name }}</h1>
            <div v-if="detail" class="badges">
              <LabelPill :label="detail.label" />
              <span v-if="nowScores" class="chip num" :data-sign="momentumSign">
                <component :is="momentumIcon" class="chip-icon" aria-hidden="true" />
                Élan {{ signedNumber(nowScores.momentum) }}
              </span>
            </div>
            <p v-if="product.aliases.length" class="aliases">
              <Search aria-hidden="true" />
              <span>On cherche aussi</span>
              <span v-for="alias in product.aliases" :key="alias" class="alias">{{ alias }}</span>
            </p>
          </template>
          <template v-else>
            <span class="skeleton sk-line short" />
            <span class="skeleton sk-line title" />
          </template>
        </div>

        <div v-if="detail" class="sections">
          <section class="panel surface rise" style="--i: 0" aria-labelledby="h-radar">
            <h2 id="h-radar" class="panel-title">Radar sur 3 horizons</h2>
            <div class="rings">
              <div v-for="(key, index) in RING_ORDER" :key="key" class="ring-cell" :data-horizon="key">
                <ScoreRing size="lg" :value="detail.radar[key]?.score ?? null" :caption="SCORE_TEXT[key]" :delay="index * 120" />
                <span class="ring-name">{{ HORIZON_TEXT[key] }}</span>
              </div>
            </div>
          </section>

          <section v-if="nowScores" class="panel surface rise" style="--i: 1" aria-labelledby="h-balance">
            <h2 id="h-balance" class="panel-title">Demande face à l’offre</h2>
            <TensionBar :demand="nowScores.demand_score" :supply="nowScores.supply_score" />
            <p class="verdict" :data-label="verdict.label">
              <component :is="verdict.icon" aria-hidden="true" />
              <span>
                <strong>{{ verdict.title }}</strong>
                {{ verdict.text }}
              </span>
            </p>
          </section>

          <section v-if="detail.history.length > 1" class="panel surface rise" style="--i: 2" aria-labelledby="h-history">
            <h2 id="h-history" class="panel-title">
              Évolution
              <span class="panel-note">{{ detail.history.length }} derniers relevés</span>
            </h2>
            <TrendChart :points="detail.history" />
          </section>

          <section v-if="product?.description" class="panel surface rise" style="--i: 3" aria-labelledby="h-about">
            <h2 id="h-about" class="panel-title">À propos</h2>
            <p class="prose">{{ product.description }}</p>
          </section>

          <section v-if="product?.where_to_find" class="panel surface rise where" style="--i: 4" aria-labelledby="h-where">
            <span class="where-icon" aria-hidden="true"><MapPin /></span>
            <div>
              <h2 id="h-where" class="panel-title">Où le trouver</h2>
              <p class="prose">{{ product.where_to_find }}</p>
            </div>
          </section>

          <section class="panel surface rise" style="--i: 5" aria-labelledby="h-sources">
            <h2 id="h-sources" class="panel-title">Sources de données</h2>
            <ul class="sources">
              <li v-for="source in detail.product.sources" :key="source.id" :data-health="source.health">
                <span class="source-icon" aria-hidden="true">
                  <ShieldCheck v-if="source.collectable" />
                  <ShieldOff v-else />
                </span>
                <span class="source-text">
                  <strong>{{ source.name }}</strong>
                  <small>{{ sourceStatus(source) }}</small>
                </span>
              </li>
              <li v-if="!detail.product.sources.length" class="empty">Aucune source liée pour l’instant.</li>
            </ul>
            <p class="legal">
              <Lock aria-hidden="true" />
              Sources publiques ou consenties uniquement. Aucun message privé, aucun numéro, aucun scraping.
            </p>
          </section>

          <p v-if="capturedAt" class="stamp">Dernier relevé {{ timeAgo(capturedAt) }}</p>
        </div>

        <div v-else class="sections" aria-busy="true">
          <div class="skeleton sk-panel" />
          <div class="skeleton sk-panel small" />
        </div>
      </div>
    </template>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  ArrowDownRight,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Lock,
  MapPin,
  Scale,
  Search,
  Share2,
  ShieldCheck,
  ShieldOff,
  TrendingDown,
  TrendingUp,
} from "lucide-vue-next";
import LabelPill from "../components/LabelPill.vue";
import ScoreRing from "../components/ScoreRing.vue";
import StateBlock from "../components/StateBlock.vue";
import TensionBar from "../components/TensionBar.vue";
import TrendChart from "../components/TrendChart.vue";
import {
  HORIZON_TEXT,
  HORIZONS,
  SCORE_TEXT,
  type Horizon,
  type SourceBrief,
  type TrendLabel,
} from "../api";
import { toast } from "../composables/useApp";
import { signedNumber, timeAgo } from "../lib/format";
import { useRadarStore } from "../stores/radar";

const props = defineProps<{ slug: string }>();

const RING_ORDER: Horizon[] = ["now", "past", "future"];
/** Demand − supply gap (points) above which we call it an opportunity / saturation. */
const BALANCE_GAP = 10;

const router = useRouter();
const radar = useRadarStore();

const from = computed<Horizon>(() => {
  const value = router.currentRoute.value.query.from;
  return typeof value === "string" && (HORIZONS as string[]).includes(value) ? (value as Horizon) : "now";
});

const slot = computed(() => radar.details[props.slug]);
const detail = computed(() => slot.value?.data ?? null);
// Radar rows already carry the catalogue card: render the hero before the API answers.
const product = computed(() => detail.value?.product ?? radar.productPreview(props.slug));

const gallery = computed(() => {
  if (!product.value) return [];
  const urls = [product.value.image_url, ...product.value.gallery].filter(Boolean);
  return [...new Set(urls)];
});

const nowScores = computed(() => detail.value?.radar.now ?? null);
const capturedAt = computed(() => nowScores.value?.captured_at ?? null);

const momentumSign = computed(() => {
  const value = nowScores.value?.momentum ?? 0;
  return value > 0 ? "up" : value < 0 ? "down" : "flat";
});
const momentumIcon = computed(() =>
  momentumSign.value === "up" ? ArrowUpRight : momentumSign.value === "down" ? ArrowDownRight : ArrowRight,
);

const verdict = computed(() => {
  const scores = nowScores.value;
  const gap = scores ? scores.demand_score - scores.supply_score : 0;
  if (gap >= BALANCE_GAP) {
    return {
      label: "rising" as TrendLabel,
      icon: TrendingUp,
      title: "Opportunité.",
      text: `La demande dépasse l’offre de ${gap} points : il y a de la place pour vendre.`,
    };
  }
  if (gap <= -BALANCE_GAP) {
    return {
      label: "falling" as TrendLabel,
      icon: TrendingDown,
      title: "Marché saturé.",
      text: `L’offre dépasse la demande de ${-gap} points : les prix risquent de baisser.`,
    };
  }
  return {
    label: "stable" as TrendLabel,
    icon: Scale,
    title: "Équilibre.",
    text: "L’offre suit à peu près la demande en ce moment.",
  };
});

function sourceStatus(source: SourceBrief): string {
  if (!source.collectable) return `${source.kind_label} · non collectée pour l’instant`;
  if (source.health === "ok" && source.last_success_at) {
    return `${source.kind_label} · collecte réussie ${timeAgo(source.last_success_at)}`;
  }
  if (source.health === "error") return `${source.kind_label} · dernière collecte en échec`;
  return `${source.kind_label} · en attente de la première collecte`;
}

// Carousel
const carouselEl = ref<HTMLElement | null>(null);
const slide = ref(0);
function onCarousel() {
  const el = carouselEl.value;
  if (!el || !el.clientWidth) return;
  slide.value = Math.round(el.scrollLeft / el.clientWidth);
}
function goTo(index: number) {
  const el = carouselEl.value;
  el?.scrollTo({ left: index * el.clientWidth, behavior: "smooth" });
}

function goBack() {
  // Real history entry inside the app → native back (keeps scroll); deep link → radar.
  if (window.history.state?.back) router.back();
  else router.push(`/${from.value}`);
}

async function share() {
  if (!product.value) return;
  const url = window.location.origin + router.resolve(`/article/${props.slug}`).href;
  const label = detail.value ? ` (${nowScores.value?.score ?? "?"}/100)` : "";
  const data = {
    title: `${product.value.name} · Firona`,
    text: `${product.value.name}${label} sur le radar du marché malgache`,
    url,
  };
  try {
    if (navigator.share) {
      await navigator.share(data);
      return;
    }
    await navigator.clipboard.writeText(url);
    toast("Lien copié", "success");
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") return;
    toast("Partage impossible sur cet appareil", "error");
  }
}

function load(force = false) {
  radar.detailEntry(props.slug);
  radar.loadDetail(props.slug, { force }).catch(() => undefined);
}

function reload() {
  load(true);
}

watch(
  () => props.slug,
  () => {
    slide.value = 0;
    load();
  },
  { immediate: true },
);
</script>

<style scoped>
.detail {
  position: relative;
  padding-bottom: calc(var(--safe-b) + 32px);
}

/* ---- Top bar (floating, solidifies on scroll) ---- */
.topbar {
  position: fixed;
  inset: 0 0 auto;
  z-index: 20;
  max-width: var(--page-max);
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: calc(var(--safe-t) + 8px) 12px 8px;
  view-transition-name: topbar;
}

.topbar::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  opacity: 0;
  /* More opaque than the app bar: the title sits on top of busy charts. */
  background: rgb(var(--bg-rgb) / 0.9);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
}

.topbar-title {
  flex: 1;
  min-width: 0;
  font-weight: 750;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0;
  transform: translateY(6px);
}

.topbar .icon-btn:last-child {
  margin-left: auto;
}

@supports (animation-timeline: scroll()) {
  .topbar::before {
    animation: topbar-in linear both;
    animation-timeline: scroll(root);
    animation-range: 140px 220px;
  }
  .topbar-title {
    animation: topbar-title linear both;
    animation-timeline: scroll(root);
    animation-range: 200px 260px;
  }
}

@keyframes topbar-in {
  to {
    opacity: 1;
  }
}

@keyframes topbar-title {
  to {
    opacity: 1;
    transform: none;
  }
}

/* ---- Hero ---- */
.hero {
  position: relative;
  height: min(62vw, 46vh, 22rem);
  background: var(--surface-2);
}

.carousel {
  display: flex;
  height: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  overscroll-behavior-x: contain;
  view-transition-name: hero;
}

.carousel::-webkit-scrollbar {
  display: none;
}

.carousel img {
  flex: none;
  width: 100%;
  height: 100%;
  object-fit: cover;
  scroll-snap-align: center;
}

.placeholder {
  flex: none;
  width: 100%;
  display: grid;
  place-items: center;
  font-size: 5rem;
  font-weight: 800;
  color: var(--accent);
}

.carousel.skeleton {
  border-radius: 0;
}

.shade {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(180deg, rgb(var(--bg-rgb) / 0.55) 0%, transparent 28%),
    linear-gradient(0deg, var(--bg) 0%, transparent 38%);
}

.dots {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 34px;
  display: flex;
  justify-content: center;
  gap: 2px;
}

.dots button {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
}

.dots button::before {
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: rgb(var(--ink-rgb) / 0.45);
  transition:
    width var(--dur-3) var(--ease-spring),
    background-color var(--dur-2) var(--ease-out);
}

.dots button.on::before {
  width: 20px;
  background: var(--ink);
}

/* ---- Sheet ---- */
.sheet {
  position: relative;
  margin-top: -22px;
  padding: 0 var(--gutter);
}

.head {
  display: grid;
  gap: 6px;
  padding-bottom: 18px;
}

.head .eyebrow {
  color: var(--accent);
}

.name {
  font-size: clamp(1.75rem, 8vw, 2.25rem);
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 1.08;
}

.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 6px;
  animation: fade-in var(--dur-3) var(--ease-out) both;
}

.chip {
  gap: 0.3rem;
  height: 26px;
  font-size: 0.74rem;
  font-weight: 700;
}

.chip-icon {
  width: 15px;
  height: 15px;
}

.chip[data-sign="up"] {
  color: var(--rising);
}

.chip[data-sign="down"] {
  color: var(--falling);
}

.aliases {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  margin-top: 8px;
  font-size: 0.8rem;
  color: var(--muted);
}

.aliases svg {
  width: 14px;
  height: 14px;
}

.alias {
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-weight: 600;
  color: var(--ink-2);
  background: var(--surface-2);
  border: 1px solid var(--line);
}

.sk-line {
  display: block;
  height: 12px;
}

.sk-line.short {
  width: 30%;
}

.sk-line.title {
  width: 70%;
  height: 30px;
}

.sections {
  display: grid;
  gap: 12px;
}

.sk-panel {
  height: 10rem;
  border-radius: var(--r-lg);
}

.sk-panel.small {
  height: 7rem;
}

.panel {
  padding: 16px;
}

.panel-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 14px;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}

.panel-note {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0;
  text-transform: none;
}

.rings {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.ring-cell {
  display: grid;
  justify-items: center;
  gap: 8px;
}

.ring-name {
  font-size: 0.8rem;
  font-weight: 750;
  color: var(--accent);
}

.verdict {
  display: flex;
  gap: 0.7rem;
  margin-top: 14px;
  padding: 12px;
  border-radius: var(--r-md);
  font-size: 0.86rem;
  color: var(--ink-2);
  background: rgb(var(--tone-rgb) / 0.1);
  border: 1px solid rgb(var(--tone-rgb) / 0.22);
}

.verdict svg {
  flex: none;
  width: 20px;
  height: 20px;
  color: var(--tone);
}

.verdict strong {
  color: var(--tone);
}

.prose {
  color: var(--ink-2);
  font-size: 0.95rem;
  line-height: 1.6;
}

.where {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.85rem;
}

.where-icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  color: var(--accent);
  background: rgb(var(--accent-rgb) / 0.14);
}

.where-icon svg {
  width: 20px;
  height: 20px;
}

.where .panel-title {
  margin-bottom: 6px;
}

.sources {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.sources li {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 0.75rem;
  padding: 10px 12px;
  border-radius: var(--r-md);
  background: var(--surface-2);
  border: 1px solid var(--line);
}

.sources li.empty {
  display: block;
  color: var(--muted);
}

.source-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  color: var(--green);
  background: rgb(var(--green-rgb) / 0.14);
}

[data-health="error"] .source-icon {
  color: var(--falling);
  background: rgb(var(--falling-rgb) / 0.14);
}

[data-health="blocked"] .source-icon {
  color: var(--muted);
  background: var(--surface-3);
}

.source-icon svg {
  width: 18px;
  height: 18px;
}

.source-text {
  display: grid;
  min-width: 0;
}

.source-text strong {
  font-size: 0.9rem;
  font-weight: 700;
}

.source-text small {
  font-size: 0.76rem;
  color: var(--muted);
}

.legal {
  display: flex;
  gap: 0.5rem;
  margin-top: 12px;
  font-size: 0.76rem;
  color: var(--muted);
}

.legal svg {
  flex: none;
  width: 14px;
  height: 14px;
  margin-top: 2px;
}

.stamp {
  padding: 4px 0 8px;
  text-align: center;
  font-size: 0.76rem;
  color: var(--muted);
}

.missing {
  padding-top: calc(var(--safe-t) + 96px);
}
</style>
