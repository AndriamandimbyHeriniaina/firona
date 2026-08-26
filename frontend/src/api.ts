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
