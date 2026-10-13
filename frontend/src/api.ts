export type Horizon = "now" | "past" | "future";

export type TrendLabel = "rising" | "falling" | "stable" | "emerging";

export const HORIZONS: Horizon[] = ["past", "now", "future"];

export interface Category {
  id: number;
  name: string;
  slug: string;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  category: Category;
  aliases: string[];
  description: string;
  image_url: string;
  gallery: string[];
  where_to_find: string;
}

export type SourceHealth = "ok" | "error" | "never" | "blocked";

export interface SourceBrief {
  id: number;
  name: string;
  kind: string;
  kind_label: string;
  consent_granted: boolean;
  collectable: boolean;
  block_reason: string | null;
  health: SourceHealth;
  last_success_at: string | null;
}

export interface ProductDetail extends Product {
  sources: SourceBrief[];
}

export interface HorizonScores {
  score: number;
  demand_score: number;
  supply_score: number;
  momentum: number;
  emerging_score: number;
  label: TrendLabel;
  captured_at: string;
}

export interface HistoryPoint {
  captured_at: string;
  demand_score: number;
  supply_score: number;
}

export interface RadarItem {
  product: Product;
  horizon: Horizon;
  score: number;
  demand_score: number;
  supply_score: number;
  momentum: number;
  emerging_score: number;
  label: TrendLabel;
  captured_at: string;
}

export interface ProductDetailPayload {
  product: ProductDetail;
  radar: Partial<Record<Horizon, HorizonScores>>;
  history: HistoryPoint[];
  label: TrendLabel;
}

export const LABEL_TEXT: Record<TrendLabel, string> = {
  rising: "En hausse",
  falling: "En baisse",
  stable: "Stable",
  emerging: "À surveiller",
};

export const HORIZON_TEXT: Record<Horizon, string> = {
  now: "Maintenant",
  past: "Passé",
  future: "Futur",
};

/** What the main score means on each horizon (card ring caption). */
export const SCORE_TEXT: Record<Horizon, string> = {
  now: "Demande",
  past: "Saison",
  future: "Émergence",
};

const REQUEST_TIMEOUT_MS = 12_000;

/** Error with a French message that can be shown as-is in the UI. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status = 0,
  ) {
    super(message);
  }
}

async function getJson<T>(url: string, notFound: string): Promise<T> {
  const controller = new AbortController();
  // One deadline for headers *and* body: a stalled 3G download must not hang the store.
  const timer = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const unreachable = () =>
    new ApiError(
      navigator.onLine
        ? "Le serveur ne répond pas. Réessayez dans un instant."
        : "Pas de connexion internet.",
    );
  try {
    let response: Response;
    try {
      response = await fetch(url, {
        signal: controller.signal,
        headers: { Accept: "application/json" },
      });
    } catch {
      throw unreachable();
    }
    if (response.status === 404) throw new ApiError(notFound, 404);
    if (!response.ok) {
      throw new ApiError(`Le serveur a répondu ${response.status}. Réessayez plus tard.`, response.status);
    }
    try {
      return (await response.json()) as T;
    } catch {
      throw unreachable();
    }
  } finally {
    window.clearTimeout(timer);
  }
}

/**
 * Fetch radar rows for one time horizon.
 *
 * @example
 * const items = await fetchRadar("now");
 */
export function fetchRadar(horizon: Horizon): Promise<RadarItem[]> {
  return getJson(`/api/v1/radar/?horizon=${horizon}`, "Radar introuvable.");
}

/**
 * Fetch one article with copy, images, sources and all horizons.
 *
 * @example
 * const detail = await fetchProductDetail("telephone");
 */
export function fetchProductDetail(slug: string): Promise<ProductDetailPayload> {
  return getJson(`/api/v1/products/${encodeURIComponent(slug)}/`, "Cet article n’existe pas ou plus.");
}
