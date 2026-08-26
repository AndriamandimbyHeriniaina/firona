<template>
  <article class="card">
    <div class="meta">
      <span class="cat">{{ item.product.category.name }}</span>
      <span class="pill" :data-label="item.label">{{ labelText }}</span>
    </div>
    <h2>{{ item.product.name }}</h2>
    <div class="bar" :style="{ '--score': item.score }">
      <span />
    </div>
    <dl>
      <div>
        <dt>Score</dt>
        <dd>{{ item.score }}</dd>
      </div>
      <div>
        <dt>Demande</dt>
        <dd>{{ item.demand_score }}</dd>
      </div>
      <div>
        <dt>Offre</dt>
        <dd>{{ item.supply_score }}</dd>
      </div>
      <div>
        <dt>Élan</dt>
        <dd>{{ signedMomentum }}</dd>
      </div>
    </dl>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { RadarItem } from "../api";

const props = defineProps<{ item: RadarItem }>();

const labels: Record<RadarItem["label"], string> = {
  rising: "En hausse",
  falling: "En baisse",
  stable: "Stable",
  emerging: "À surveiller",
};

const labelText = computed(() => labels[props.item.label]);
const signedMomentum = computed(() => {
  const value = props.item.momentum;
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
});
</script>
