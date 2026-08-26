<template>
  <router-link class="card card-link" :to="to">
    <img
      v-if="item.product.image_url"
      class="thumb"
      :src="item.product.image_url"
      :alt="item.product.name"
    />
    <div class="card-body">
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
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { LABEL_TEXT, type Horizon, type RadarItem } from "../api";

const props = defineProps<{ item: RadarItem; horizon: Horizon }>();

const labelText = computed(() => LABEL_TEXT[props.item.label]);
const signedMomentum = computed(() => {
  const value = props.item.momentum;
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
});
const to = computed(() => ({
  path: `/article/${props.item.product.slug}`,
  query: { from: props.horizon },
}));
</script>
