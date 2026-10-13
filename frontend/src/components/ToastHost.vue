<template>
  <div class="toasts" :class="{ raised: raised }" role="status" aria-live="polite">
    <TransitionGroup name="toast">
      <p v-for="item in toasts" :key="item.id" class="toast" :data-tone="item.tone">
        <CircleCheck v-if="item.tone === 'success'" />
        <CircleAlert v-else-if="item.tone === 'error'" />
        <Info v-else />
        <span>{{ item.text }}</span>
      </p>
    </TransitionGroup>
    <Transition name="toast">
      <p v-if="!online" class="toast offline">
        <WifiOff />
        <span>Hors ligne · dernières données en cache</span>
      </p>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { CircleAlert, CircleCheck, Info, WifiOff } from "lucide-vue-next";
import { useOnline, useToasts } from "../composables/useApp";

defineProps<{ raised: boolean }>();

const toasts = useToasts();
const online = useOnline();
</script>

<style scoped>
.toasts {
  position: fixed;
  left: 0;
  right: 0;
  bottom: calc(var(--safe-b) + 16px);
  z-index: 40;
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 0 var(--gutter);
  pointer-events: none;
}

.toasts.raised {
  bottom: calc(var(--safe-b) + var(--nav-h) + 12px);
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  max-width: min(100%, 26rem);
  padding: 0.7rem 1rem;
  border-radius: 16px;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--ink);
  background: var(--surface-3);
  border: 1px solid var(--line-2);
  box-shadow: var(--shadow-2);
}

.toast svg {
  width: 18px;
  height: 18px;
  flex: none;
  color: var(--accent);
}

.toast[data-tone="success"] svg {
  color: var(--green);
}

.toast[data-tone="error"] svg,
.toast.offline svg {
  color: var(--falling);
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity var(--dur-3) var(--ease-out),
    transform var(--dur-3) var(--ease-spring);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}
</style>
