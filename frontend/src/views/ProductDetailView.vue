<template>
  <article class="detail">
    <router-link class="back" :to="backTo">← Radar</router-link>

    <p v-if="loading" class="status">Ouverture de l’article…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <template v-else-if="detail">
      <figure class="hero">
        <img :src="hero" :alt="detail.product.name" />
      </figure>
      <div v-if="gallery.length > 1" class="gallery">
        <button
          v-for="src in gallery"
          :key="src"
          type="button"
          :class="{ on: src === hero }"
          :aria-label="'Image ' + src"
          @click="hero = src"
        >
          <img :src="src" alt="" />
        </button>
      </div>

      <div class="meta">
        <span class="cat">{{ detail.product.category.name }}</span>
        <span class="pill" :data-label="detail.label">{{ LABEL_TEXT[detail.label] }}</span>
      </div>
      <h2>{{ detail.product.name }}</h2>
      <p v-if="detail.product.aliases.length" class="aliases">
        On cherche aussi : {{ detail.product.aliases.join(", ") }}
      </p>
      <p class="body">{{ detail.product.description }}</p>

      <section class="block">
        <h3>Où le trouver</h3>
        <p>{{ detail.product.where_to_find }}</p>
      </section>

      <section class="block">
        <h3>Sources de données</h3>
        <ul class="sources">
          <li v-for="source in detail.product.sources" :key="source.id">
            <strong>{{ source.name }}</strong>
            <span>{{ source.kind_label }}</span>
            <em v-if="source.consent_granted">consentie</em>
          </li>
          <li v-if="!detail.product.sources.length">Aucune source liée pour l’instant.</li>
        </ul>
        <p class="hint">v1 : données de démonstration. Les collecteurs légaux arrivent en v3.</p>
      </section>

      <section class="block">
        <h3>Radar</h3>
        <div class="score-grid">
          <div v-for="key in horizons" :key="key" class="score-card">
            <span>{{ HORIZON_TEXT[key] }}</span>
            <strong>{{ detail.radar[key]?.score ?? "—" }}</strong>
            <small>{{ scoreHint(key) }}</small>
          </div>
        </div>
      </section>

      <section v-if="detail.history.length" class="block">
        <h3>Demande, 15 derniers jours</h3>
        <Sparkline :values="historyDemand" label="Évolution de la demande" />
      </section>
    </template>
  </article>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import Sparkline from "../components/Sparkline.vue";
import {
  fetchProductDetail,
  HORIZON_TEXT,
  LABEL_TEXT,
  type Horizon,
  type ProductDetailPayload,
} from "../api";

const props = defineProps<{ slug: string }>();
const route = useRoute();
const detail = ref<ProductDetailPayload | null>(null);
const loading = ref(true);
const error = ref("");
const hero = ref("");
const horizons: Horizon[] = ["now", "past", "future"];

const gallery = computed(() => {
  if (!detail.value) return [];
  const urls = [detail.value.product.image_url, ...detail.value.product.gallery].filter(Boolean);
  return [...new Set(urls)];
});

const historyDemand = computed(
  () => detail.value?.history.map((point) => point.demand_score) ?? [],
);

const backTo = computed(() => {
  const from = route.query.from;
  if (from === "past" || from === "future" || from === "now") return `/${from}`;
  return "/now";
});

function scoreHint(horizon: Horizon): string {
  const row = detail.value?.radar[horizon];
  if (!row) return "Pas encore de score";
  if (horizon === "past") return `Saison ${row.score}`;
  if (horizon === "future") return `Émergence ${row.emerging_score}`;
  return `Demande ${row.demand_score} · offre ${row.supply_score}`;
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    detail.value = await fetchProductDetail(props.slug);
    hero.value = detail.value.product.image_url || gallery.value[0] || "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Impossible d’ouvrir l’article.";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => props.slug, load);
</script>
