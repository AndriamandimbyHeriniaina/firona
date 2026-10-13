/**
 * Device capabilities: reduced motion, low-end Android ("lite" mode), haptics.
 *
 * Lite mode drops the costly effects (backdrop blur, aura glow) on phones with
 * ≤ 2 GB RAM or when the user enabled Data Saver.
 */

const reducedQuery =
  typeof window !== "undefined" ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;

export function prefersReducedMotion(): boolean {
  return Boolean(reducedQuery?.matches);
}

interface NavigatorHints extends Navigator {
  deviceMemory?: number;
  connection?: { saveData?: boolean };
}

export function isLiteDevice(): boolean {
  const nav = navigator as NavigatorHints;
  const lowMemory = typeof nav.deviceMemory === "number" && nav.deviceMemory <= 2;
  const fewCores = typeof nav.hardwareConcurrency === "number" && nav.hardwareConcurrency <= 2;
  return lowMemory || fewCores || Boolean(nav.connection?.saveData);
}

/**
 * Short vibration tick on Android (no-op elsewhere or with reduced motion).
 *
 * @example
 * haptic();        // tab change
 * haptic([12, 40, 12]); // pull-to-refresh armed
 */
export function haptic(pattern: number | number[] = 8): void {
  if (prefersReducedMotion() || !("vibrate" in navigator)) return;
  try {
    navigator.vibrate(pattern);
  } catch {
    // Some WebViews throw without a user gesture; haptics are optional.
  }
}
