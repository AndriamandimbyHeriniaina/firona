<template>
  <section>
    <p v-if="loading" class="status">Lecture du radar…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <ul v-else class="list">
      <li v-for="item in items" :key="item.product.id">
        <TrendCard :item="item" />
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import TrendCard from "../components/TrendCard.vue";
import { fetchRadar, type Horizon, type RadarItem } from "../api";

const props = defineProps<{ horizon: Horizon }>();
const items = ref<RadarItem[]>([]);
const loading = ref(true);
const error = ref("");

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
