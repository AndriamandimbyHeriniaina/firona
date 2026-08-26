<template>
  <div class="shell">
    <header class="top">
      <p class="eyebrow">Marché malgache</p>
      <h1>Firona</h1>
      <p class="lede">Les articles que les gens cherchent, vendent, et qui chauffent.</p>
    </header>
    <main class="content">
      <router-view />
    </main>
    <nav class="dock" aria-label="Horizon temporel">
      <router-link to="/past">Passé</router-link>
      <router-link to="/now" class="now">Maintenant</router-link>
      <router-link to="/future">Futur</router-link>
    </nav>
  </div>
</template>

<script setup lang="ts"></script>
