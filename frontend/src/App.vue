<template>
  <div class="shell" :class="{ compact: compactHeader }">
    <header class="top">
      <p class="eyebrow">Marché malgache</p>
      <h1>Firona</h1>
      <p v-if="!compactHeader" class="lede">
        Ce que les gens cherchent, vendent, et ce qui chauffe.
      </p>
    </header>
    <main class="content">
      <router-view />
    </main>
    <nav v-if="!hideDock" class="dock" aria-label="Horizon temporel">
      <router-link to="/past">
        <span class="dock-kicker">Avant</span>
        Passé
      </router-link>
      <router-link to="/now" class="now">
        <span class="dock-kicker">Radar</span>
        Maintenant
      </router-link>
      <router-link to="/future">
        <span class="dock-kicker">Ensuite</span>
        Futur
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const hideDock = computed(() => Boolean(route.meta.hideDock));
const compactHeader = computed(() => Boolean(route.meta.compactHeader));
</script>
