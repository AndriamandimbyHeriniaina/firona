/**
 * Radar cache: one entry per horizon and per article, stale-while-revalidate.
 *
 * Cached rows render instantly (tab switch, back from an article, view
 * transitions) while a background request refreshes them.
 *
 * @example
 * const radar = useRadarStore();
 * await radar.loadHorizon("now");
 * radar.horizons.now.items;
 */

import { defineStore } from "pinia";
import { reactive, ref } from "vue";
import {
  ApiError,
  fetchProductDetail,
  fetchRadar,
  HORIZONS,
  type Horizon,
  type Product,
  type ProductDetailPayload,
  type RadarItem,
} from "../api";

/** Cached data younger than this is not refetched on navigation. */
const FRESH_MS = 60_000;

export type LoadStatus = "idle" | "loading" | "ready" | "error";

interface Entry<T> {
  data: T;
  status: LoadStatus;
  error: string;
  fetchedAt: number;
  refreshing: boolean;
}

function entry<T>(data: T): Entry<T> {
  return { data, status: "idle", error: "", fetchedAt: 0, refreshing: false };
}

function messageOf(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

export const useRadarStore = defineStore("radar", () => {
  const horizons = reactive<Record<Horizon, Entry<RadarItem[]>>>({
    past: entry<RadarItem[]>([]),
    now: entry<RadarItem[]>([]),
    future: entry<RadarItem[]>([]),
  });
  const details = reactive<Record<string, Entry<ProductDetailPayload | null>>>({});

  /** Article whose thumbnail morphs into the detail hero (view transition). */
  const activeSlug = ref<string | null>(null);

  const inflight = new Map<string, Promise<void>>();

  function dedupe(key: string, run: () => Promise<void>): Promise<void> {
    const pending = inflight.get(key);
    if (pending) return pending;
    const task = run().finally(() => inflight.delete(key));
    inflight.set(key, task);
    return task;
  }

  /** Load one horizon; returns at once when the cache is fresh unless `force`. */
  function loadHorizon(horizon: Horizon, { force = false } = {}): Promise<void> {
    const slot = horizons[horizon];
    if (!force && slot.status === "ready" && Date.now() - slot.fetchedAt < FRESH_MS) {
      return Promise.resolve();
    }
    return dedupe(`radar:${horizon}`, async () => {
      const hasData = slot.data.length > 0;
      if (hasData) slot.refreshing = true;
      else slot.status = "loading";
      try {
        slot.data = await fetchRadar(horizon);
        slot.status = "ready";
        slot.error = "";
        slot.fetchedAt = Date.now();
      } catch (err) {
        slot.error = messageOf(err, "Impossible de charger le radar.");
        // Keep showing the last rows we had; only an empty cache is an error screen.
        slot.status = hasData ? "ready" : "error";
        throw err;
      } finally {
        slot.refreshing = false;
      }
    });
  }

  /** Warm the other horizons so swipes and tab taps render without a spinner. */
  function prefetchHorizons(except: Horizon) {
    for (const horizon of HORIZONS) {
      if (horizon !== except) loadHorizon(horizon).catch(() => undefined);
    }
  }

  /** Catalogue fields we already know from a radar list (instant detail hero). */
  function productPreview(slug: string): Product | null {
    for (const horizon of HORIZONS) {
      const row = horizons[horizon].data.find((item) => item.product.slug === slug);
      if (row) return row.product;
    }
    return null;
  }

  function detailEntry(slug: string): Entry<ProductDetailPayload | null> {
    if (!details[slug]) details[slug] = entry<ProductDetailPayload | null>(null);
    return details[slug];
  }

  function loadDetail(slug: string, { force = false } = {}): Promise<void> {
    const slot = detailEntry(slug);
    if (!force && slot.status === "ready" && Date.now() - slot.fetchedAt < FRESH_MS) {
      return Promise.resolve();
    }
    return dedupe(`detail:${slug}`, async () => {
      const hasData = slot.data !== null;
      if (hasData) slot.refreshing = true;
      else slot.status = "loading";
      try {
        slot.data = await fetchProductDetail(slug);
        slot.status = "ready";
        slot.error = "";
        slot.fetchedAt = Date.now();
      } catch (err) {
        slot.error = messageOf(err, "Impossible d’ouvrir l’article.");
        slot.status = hasData ? "ready" : "error";
        throw err;
      } finally {
        slot.refreshing = false;
      }
    });
  }

  return {
    horizons,
    details,
    activeSlug,
    loadHorizon,
    prefetchHorizons,
    productPreview,
    detailEntry,
    loadDetail,
  };
});
