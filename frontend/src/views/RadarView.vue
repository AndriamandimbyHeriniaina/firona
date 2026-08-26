<template>
  <section>
    <header class="horizon-head">
      <h2>{{ heading }}</h2>
      <p>{{ sub }}</p>
    </header>
    <p v-if="loading" class="status">Lecture du radar…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <ul v-else class="list">
      <li v-for="item in items" :key="item.product.id">
        <TrendCard :item="item" :horizon="horizon" />
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import TrendCard from "../components/TrendCard.vue";
import { fetchRadar, HORIZON_TEXT, type Horizon, type RadarItem } from "../api";

const props = defineProps<{ horizon: Horizon }>();
const items = ref<RadarItem[]>([]);
const loading = ref(true);
const error = ref("");

const heading = computed(() => HORIZON_TEXT[props.horizon]);
const sub = computed(() => {
  if (props.horizon === "past") return "Ce qui se cherchait d’habitude à cette période.";
  if (props.horizon === "future") return "Ce qui pourrait monter dans les semaines qui viennent.";
  return "Les articles les plus cherchés en ce moment.";
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    items.value = await fetchRadar(props.horizon);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Impossible de charger le radar.";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => props.horizon, load);
</script>
