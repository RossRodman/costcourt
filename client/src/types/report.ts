export type ReportFormat = "markdown" | "html" | "json";

export interface ReportSummary {
  id: string;
  created_at: string;
  estimate_id: string;
  estimate_title: string;
  location: string | null;
  currency: string;
  rounds: number;
  rulings: number;
  confidence: number;
  original_total: number;
  revised_total: number;
  delta_pct: number;
  demo: boolean;
}
