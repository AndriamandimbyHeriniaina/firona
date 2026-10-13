/** French formatting helpers shared by the radar screens. */

const relative = new Intl.RelativeTimeFormat("fr", { numeric: "auto" });
const signed = new Intl.NumberFormat("fr", {
  signDisplay: "exceptZero",
  maximumFractionDigits: 1,
});
const shortDay = new Intl.DateTimeFormat("fr", {
  weekday: "short",
  day: "numeric",
  month: "short",
});
const dayMonth = new Intl.DateTimeFormat("fr", { day: "numeric", month: "short" });

const STEPS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 31_536_000],
  ["month", 2_592_000],
  ["week", 604_800],
  ["day", 86_400],
  ["hour", 3_600],
  ["minute", 60],
];

/**
 * "il y a 3 heures", "hier", "à l’instant".
 *
 * @example
 * timeAgo("2026-10-12T08:00:00Z") // "il y a 2 heures"
 */
export function timeAgo(iso: string | null | undefined, now = Date.now()): string {
  if (!iso) return "";
  const seconds = Math.round((new Date(iso).getTime() - now) / 1000);
  if (Math.abs(seconds) < 60) return "à l’instant";
  for (const [unit, size] of STEPS) {
    if (Math.abs(seconds) >= size) return relative.format(Math.round(seconds / size), unit);
  }
  return "à l’instant";
}

/** "+6", "-3,5", "0". */
export function signedNumber(value: number): string {
  return signed.format(Math.round(value * 10) / 10);
}

/** "lun. 6 oct." */
export function formatShortDay(iso: string): string {
  return shortDay.format(new Date(iso));
}

/** "6 oct." */
export function formatDayMonth(iso: string): string {
  return dayMonth.format(new Date(iso));
}

/** Most recent `captured_at` of a list (ISO), or null. */
export function latestIso(values: string[]): string | null {
  let best: string | null = null;
  let bestTime = -Infinity;
  for (const value of values) {
    const time = new Date(value).getTime();
    if (time > bestTime) {
      best = value;
      bestTime = time;
    }
  }
  return best;
}

/** Stable 32-bit hash so a product keeps the same radar bearing everywhere. */
export function hashString(text: string): number {
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}
