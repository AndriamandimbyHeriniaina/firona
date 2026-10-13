import { onBeforeUnmount, onMounted, reactive, type Ref } from "vue";
import { haptic } from "../lib/device";

/** Pull distance (px, after damping) that triggers a refresh. */
export const PULL_TRIGGER = 72;
const PULL_MAX = 120;
const SWIPE_DISTANCE = 64;
const SWIPE_VELOCITY = 0.45; // px per ms
const AXIS_LOCK = 10;

export interface GestureOptions {
  /** Called with "left" (finger moved left → next horizon) or "right". */
  onSwipe?: (direction: "left" | "right") => boolean | void;
  /** Whether a swipe in this direction leads somewhere (else rubber-band). */
  canSwipe?: (direction: "left" | "right") => boolean;
  onRefresh?: () => Promise<unknown>;
}

/**
 * Horizontal swipe between horizons + pull-to-refresh, on passive listeners.
 *
 * The element should have `touch-action: pan-y`: the browser keeps native
 * vertical scrolling and leaves horizontal moves to us without preventDefault.
 *
 * @example
 * const gesture = useTouchGestures(pageEl, { onSwipe, canSwipe, onRefresh });
 * // gesture.dx (drag offset), gesture.pull (0..120), gesture.refreshing
 */
export function useTouchGestures(target: Ref<HTMLElement | null>, options: GestureOptions) {
  const state = reactive({
    dx: 0,
    pull: 0,
    dragging: false,
    refreshing: false,
  });

  let startX = 0;
  let startY = 0;
  let startTime = 0;
  let axis: "x" | "y" | null = null;
  let armed = false;
  let atTop = false;

  const onStart = (event: TouchEvent) => {
    if (event.touches.length !== 1 || state.refreshing) return;
    const touch = event.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;
    startTime = performance.now();
    axis = null;
    armed = false;
    atTop = window.scrollY <= 0;
  };

  const onMove = (event: TouchEvent) => {
    if (event.touches.length !== 1 || state.refreshing) return;
    const touch = event.touches[0];
    const dx = touch.clientX - startX;
    const dy = touch.clientY - startY;

    if (!axis) {
      if (Math.abs(dx) < AXIS_LOCK && Math.abs(dy) < AXIS_LOCK) return;
      axis = Math.abs(dx) > Math.abs(dy) * 1.2 ? "x" : "y";
    }

    if (axis === "x" && options.onSwipe) {
      const direction = dx < 0 ? "left" : "right";
      const open = options.canSwipe?.(direction) ?? true;
      // Rubber-band when there is no horizon on that side.
      state.dx = open ? dx * 0.55 : dx * 0.18;
      state.dragging = true;
      return;
    }

    if (axis === "y" && options.onRefresh && atTop && dy > 0 && window.scrollY <= 0) {
      // Damped pull: fast at first, heavier near the max.
      state.pull = Math.min(PULL_MAX, dy * 0.5 * (1 - Math.min(dy, 400) / 1200));
      state.dragging = true;
      if (!armed && state.pull >= PULL_TRIGGER) {
        armed = true;
        haptic(10);
      } else if (armed && state.pull < PULL_TRIGGER) {
        armed = false;
      }
    }
  };

  const onEnd = async () => {
    if (!state.dragging) return;
    state.dragging = false;

    if (axis === "x") {
      const elapsed = Math.max(1, performance.now() - startTime);
      const raw = state.dx / 0.55;
      const direction = raw < 0 ? "left" : "right";
      const fast = Math.abs(raw) / elapsed > SWIPE_VELOCITY;
      const open = options.canSwipe?.(direction) ?? true;
      if (open && (Math.abs(raw) > SWIPE_DISTANCE || (fast && Math.abs(raw) > 24))) {
        haptic();
        // Keep the offset: the view transition slides on from here.
        if (options.onSwipe?.(direction) !== false) return;
      }
      state.dx = 0;
      return;
    }

    if (axis === "y" && options.onRefresh) {
      if (state.pull >= PULL_TRIGGER) {
        state.refreshing = true;
        state.pull = PULL_TRIGGER * 0.75;
        try {
          await options.onRefresh();
        } catch {
          // The caller reports errors (toast); the indicator just closes.
        } finally {
          state.refreshing = false;
          state.pull = 0;
        }
      } else {
        state.pull = 0;
      }
    }
  };

  const onCancel = () => {
    state.dragging = false;
    if (!state.refreshing) state.pull = 0;
    state.dx = 0;
  };

  onMounted(() => {
    const el = target.value;
    if (!el) return;
    el.addEventListener("touchstart", onStart, { passive: true });
    el.addEventListener("touchmove", onMove, { passive: true });
    el.addEventListener("touchend", onEnd, { passive: true });
    el.addEventListener("touchcancel", onCancel, { passive: true });
  });

  onBeforeUnmount(() => {
    const el = target.value;
    if (!el) return;
    el.removeEventListener("touchstart", onStart);
    el.removeEventListener("touchmove", onMove);
    el.removeEventListener("touchend", onEnd);
    el.removeEventListener("touchcancel", onCancel);
  });

  return state;
}
