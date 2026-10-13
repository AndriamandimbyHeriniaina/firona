<template>
  <div v-reveal class="tension" :class="{ compact, 'is-in': !animate, still: !animate }" :style="{ '--d': demand / 100, '--s': supply / 100 }">
    <div class="row">
      <span class="name">Demande</span>
      <span class="track"><i class="fill demand" /></span>
      <span class="val num">{{ demand }}</span>
    </div>
    <div class="row">
      <span class="name">Offre</span>
      <span class="track"><i class="fill supply" /></span>
      <span class="val num">{{ supply }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{ demand: number; supply: number; compact?: boolean; animate?: boolean }>(),
  { compact: false, animate: true },
);
</script>

<style scoped>
.tension {
  display: grid;
  gap: 7px;
}

.row {
  display: grid;
  grid-template-columns: 4.6rem 1fr 1.8rem;
  align-items: center;
  gap: 0.6rem;
}

.compact .row {
  grid-template-columns: 3.9rem 1fr 1.6rem;
  gap: 0.5rem;
}

.name {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--muted);
}

.val {
  font-size: 0.8rem;
  font-weight: 700;
  text-align: right;
  color: var(--ink-2);
}

.track {
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
  background: rgb(var(--ink-rgb) / 0.08);
}

.compact .track {
  height: 5px;
}

/* scaleX on the compositor instead of animating width. */
.fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  transform-origin: left;
  transform: scaleX(0);
  transition: transform 1000ms var(--ease-out) 120ms;
}

.still .fill {
  transition: none;
}

.demand {
  background: linear-gradient(90deg, rgb(var(--green-rgb) / 0.55), var(--green));
}

.supply {
  background: linear-gradient(90deg, rgb(var(--gold-rgb) / 0.55), var(--gold));
  transition-delay: 220ms;
}

.is-in .demand {
  transform: scaleX(var(--d));
}

.is-in .supply {
  transform: scaleX(var(--s));
}
</style>
