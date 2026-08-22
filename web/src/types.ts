export type ChartKind =
  | "bar"
  | "line"
  | "pie"
  | "forest"
  | "box"
  | "scatter"
  | "diverging"
  | "funnel";

export interface ChartSpec {
  kind: ChartKind;
  title: string;
  note?: string;
  unit?: string;
  xLabel?: string;
  yLabel?: string;
  series?: string[];
  data: Record<string, string | number>[];
}

export interface Slide {
  id: string;
  section: string;
  kicker: string;
  title: string;
  subtitle?: string;
  narrative: string;
  bullets?: string[];
  callout?: { label: string; text: string };
  chart?: ChartSpec;
  table?: { headers: string[]; rows: string[][] };
  layout: "title" | "insight" | "split" | "chart" | "grid" | "close";
}

export interface Intervention {
  id: string;
  name: string;
  promise: string;
  lever: string;
  segment: string;
  effort: string;
  impact: number;
  feasibility: number;
  mlr: string;
  kill: string;
}

export interface ExtractedBrief {
  brand: string;
  product: string;
  therapy_area: string;
  indication: string;
  market: string;
  business_goal: string;
  target_specialties: string[];
  hcp_segments: string[];
  brand_evidence: string[];
  existing_evidence: string[];
  evolving_evidence: string[];
  guidelines: string[];
  hcp_insights: string[];
  competitors: string[];
  access_and_cost: string[];
  constraints: string[];
  notes: string;
  source_files: string[];
  raw_text: string;
  extraction_notes: string[];
}

export interface StrategyPack {
  meta: {
    brand: string;
    product: string;
    therapyArea: string;
    market: string;
    generatedAt: string;
    mode: string;
    doctrine: string;
    angleId: string;
    source?: string;
  };
  brief: ExtractedBrief;
  doctrine: {
    id: string;
    name: string;
    thesis: string;
    enemy: string;
    bet: string;
    whyNovel: string;
  };
  slides: Slide[];
  interventions: Intervention[];
  dashboard: {
    kpis: {
      id: string;
      label: string;
      value: number;
      target: number;
      unit: string;
      tone: string;
    }[];
    funnel: { name: string; value: number }[];
    revenue: Record<string, string | number>[];
    segments: { name: string; impact: number; ready: number; cost: number }[];
    evidenceMix: { name: string; value: number }[];
    alerts: { level: string; text: string }[];
    governance: { cadence: string; forum: string; looksAt: string }[];
  };
}

export interface FilePreview {
  filename: string;
  suffix: string;
  bytes: number;
  pages: number | null;
  notes: string[];
  chars: number;
  preview: string;
}

export type TabId = "briefs" | "deck" | "dashboard";
