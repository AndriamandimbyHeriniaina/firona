/**
 * Route changes through the View Transitions API (Chrome / Android WebView 111+).
 *
 * The router waits while the browser snapshots the old screen, then the new
 * DOM is captured once Vue has rendered and scroll is restored. CSS in
 * styles.css animates the snapshots from `html[data-vt="<direction>"]`.
 *
 * @example
 * installViewTransitions(router); // returns false when unsupported
 */

import { nextTick } from "vue";
import type { RouteLocationNormalized, Router } from "vue-router";
import { prefersReducedMotion } from "./device";

export type NavDirection = "left" | "right" | "forward" | "back" | "fade";

/** Horizon order on screen: Passé | Maintenant | Futur. */
export function navDirection(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
): NavDirection {
  const toIndex = to.meta.index;
  const fromIndex = from.meta.index;
  if (typeof toIndex === "number" && typeof fromIndex === "number") {
    if (toIndex === fromIndex) return "fade";
    return toIndex > fromIndex ? "left" : "right";
  }
  if (to.meta.depth && !from.meta.depth) return "forward";
  if (!to.meta.depth && from.meta.depth) return "back";
  return "fade";
}

export const supportsViewTransitions =
  typeof document !== "undefined" && "startViewTransition" in document;

/** Hand-off between the router (DOM ready) and one view transition (capture new state). */
interface Handoff {
  released: boolean;
  done?: () => void;
}

export function installViewTransitions(router: Router): boolean {
  if (!supportsViewTransitions) return false;
  const root = document.documentElement;
  // Keyed by the target route object, which vue-router passes to every guard and
  // to afterEach/onError of the same navigation: quick successive taps never
  // release each other's transition.
  const handoffs = new WeakMap<RouteLocationNormalized, Handoff>();

  const release = (to: RouteLocationNormalized) => {
    const handoff = handoffs.get(to);
    if (!handoff) return;
    handoffs.delete(to);
    handoff.released = true;
    handoff.done?.();
  };

  router.beforeResolve((to, from) => {
    // First load, same URL, or user asked for less motion: plain navigation.
    if (!from.matched.length || to.fullPath === from.fullPath || prefersReducedMotion()) return;
    root.dataset.vt = navDirection(to, from);
    return new Promise<void>((resolve) => {
      const handoff: Handoff = { released: false };
      handoffs.set(to, handoff);
      const transition = document.startViewTransition(
        () =>
          new Promise<void>((done) => {
            handoff.done = done;
            resolve();
            // Navigation already settled (cancelled / superseded): capture now.
            if (handoff.released) done();
          }),
      );
      // Skipped transitions reject `ready`; that is expected, not an error.
      transition.ready.catch(() => undefined);
      transition.finished.finally(() => {
        delete root.dataset.vt;
      });
    });
  });

  router.afterEach(async (to) => {
    if (!handoffs.has(to)) return;
    await nextTick();
    // vue-router restores scroll after its own nextTick; let that land first.
    await new Promise((resolve) => window.setTimeout(resolve, 0));
    release(to);
  });

  router.onError((_error, to) => release(to));
  return true;
}
