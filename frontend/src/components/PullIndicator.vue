<template>
  <div
    class="pull"
    :class="{ armed, busy: refreshing, moving: dragging }"
    :style="{ '--y': `${distance}px`, '--turn': `${progress * 270}deg`, '--o': Math.min(1, progress * 1.4) }"
    aria-hidden="true"
  >
    <span class="knob glass-bar">
      <RefreshCw />
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RefreshCw } from "lucide-vue-next";
import { PULL_TRIGGER } from "../composables/useTouchGestures";

const props = defineProps<{ distance: number; refreshing: boolean; dragging: boolean }>();

const progress = computed(() => Math.min(1, props.distance / PULL_TRIGGER));
const armed = computed(() => props.distance >= PULL_TRIGGER);
</script>

<style scoped>
.pull {
  position: fixed;
  top: calc(var(--safe-t) + var(--bar-h) - 44px);
  left: 50%;
  z-index: 15;
  pointer-events: none;
  transform: translate(-50%, var(--y));
  opacity: var(--o);
  transition:
    transform var(--dur-3) var(--ease-spring),
    opacity var(--dur-2) var(--ease-out);
}

.pull.moving {
  transition: none;
}

.knob {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: var(--muted);
  background: var(--surface-3);
  border: 1px solid var(--line-2);
  box-shadow: var(--shadow-2);
  transition:
    color var(--dur-2) var(--ease-out),
    background-color var(--dur-2) var(--ease-out);
}

.knob svg {
  width: 20px;
  height: 20px;
  transform: rotate(var(--turn));
}

.armed .knob,
.busy .knob {
  color: var(--on-accent);
  background: var(--accent);
}

.busy .knob svg {
  animation: spin 0.8s linear infinite;
}
</style>
