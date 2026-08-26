export type Horizon = "now" | "past" | "future";

export type TrendLabel = "rising" | "falling" | "stable" | "emerging";

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

export interface SourceBrief {
  id: number;
  name: string;
  kind: string;
  kind_label: string;
  consent_granted: boolean;
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

/**
 * Fetch radar rows for one time horizon.
 *
 * @example
 * const items = await fetchRadar("now");
 */
export async function fetchRadar(horizon: Horizon): Promise<RadarItem[]> {
  const response = await fetch(`/api/v1/radar/?horizon=${horizon}`);
  if (!response.ok) {
    throw new Error(`Radar request failed (${response.status})`);
  }
  return response.json();
}

/**
 * Fetch one article with copy, images, sources and all horizons.
 *
 * @example
 * const detail = await fetchProductDetail("telephone");
 */
export async function fetchProductDetail(slug: string): Promise<ProductDetailPayload> {
  const response = await fetch(`/api/v1/products/${slug}/`);
  if (!response.ok) {
    throw new Error(`Article introuvable (${response.status})`);
  }
  return response.json();
}
