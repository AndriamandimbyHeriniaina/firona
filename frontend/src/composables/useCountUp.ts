import { onBeforeUnmount, ref, watch, type Ref } from "vue";
import { prefersReducedMotion } from "../lib/device";

const easeOutCubic = (t: number) => 1 - (1 - t) ** 3;

/**
 * Animated integer that eases from its previous value to `target`.
 *
 * @example
 * const shown = useCountUp(() => props.score, { delay: 120 });
 * const still = useCountUp(() => props.score, { instant: true }); // no intro
 * // template: {{ shown }}
 */
export function useCountUp(
  target: () => number,
  {
    duration = 900,
    delay = 0,
    instant = false,
  }: { duration?: number; delay?: number; instant?: boolean } = {},
): Ref<number> {
  const shown = ref(instant || prefersReducedMotion() ? Math.round(target()) : 0);
  let frame = 0;
  let timer = 0;

  const run = (to: number) => {
    cancelAnimationFrame(frame);
    window.clearTimeout(timer);
    if (prefersReducedMotion()) {
      shown.value = Math.round(to);
      return;
    }
    const from = shown.value;
    if (from === Math.round(to)) return;
    timer = window.setTimeout(() => {
      const start = performance.now();
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / duration);
        shown.value = Math.round(from + (to - from) * easeOutCubic(t));
        if (t < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    }, delay);
  };

  watch(target, run, { immediate: true });
  onBeforeUnmount(() => {
    cancelAnimationFrame(frame);
    window.clearTimeout(timer);
  });
  return shown;
}
