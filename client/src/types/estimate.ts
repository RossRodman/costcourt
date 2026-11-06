export type Unit = "m" | "m2" | "m3" | "kg" | "t" | "pcs" | "hr" | "day" | "ls";

export type Category =
  | "site_prep"
  | "earthworks"
  | "concrete"
  | "masonry"
  | "steel"
  | "carpentry"
  | "roofing"
  | "mep"
  | "finishes"
  | "equipment"
  | "general";

export interface LineItem {
  id: string;
  description: string;
  category: Category;
  unit: Unit;
  quantity: number;
  unit_rate: number;
  notes?: string | null;
  total: number;
}

export interface Markups {
  overhead: number;
  profit: number;
  contingency: number;
  tax: number;
}

export interface EstimateTotals {
  direct_cost: number;
  overhead: number;
  profit: number;
  contingency: number;
  subtotal: number;
  tax: number;
  grand_total: number;
}

export interface Estimate {
  id: string;
  title: string;
  scope: string;
  location?: string | null;
  currency: string;
  items: LineItem[];
  markups: Markups;
  totals: EstimateTotals;
}

export interface EstimateSummary {
  id: string;
  title: string;
  location: string | null;
  currency: string;
  item_count: number;
  grand_total: number;
}
