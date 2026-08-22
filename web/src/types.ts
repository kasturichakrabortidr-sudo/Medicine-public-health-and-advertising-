export type ChartKind =
  | "bar"
  | "line"
  | "pie"
  | "forest"
  | "box"
  | "scatter"
  | "diverging"
  | "funnel"
  | "people"
  | "compare"
  | "spine";

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
  layout: "title" | "insight" | "split" | "chart" | "grid" | "close" | "infographic";
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
  evidenceAnchor?: string;
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
    scienceLead?: string;
    scienceAnchor?: string;
  };
  evidence?: {
    lead: CampaignLead;
    records: EvidenceRecord[];
    gaps: { stream: string; item: string; status: string; needed: string }[];
    pubmed: { pmid: string; title: string; citation: string; url: string; year?: number; journal?: string; doi?: string; note?: string }[];
    validatedCount: number;
    gapCount: number;
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
    campaignLead?: CampaignLead;
    citations?: EvidenceRecord[];
    evidenceGaps?: { stream: string; item: string; status: string; needed: string }[];
    pubmed?: { pmid: string; title: string; citation: string; url: string }[];
    meaning?: Record<string, string | number>[];
    compare?: Record<string, string | number>[];
    spine?: Record<string, string | number>[];
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

export interface EvidenceRecord {
  id: string;
  stream: string;
  trial: string;
  short: string;
  title: string;
  authors: string;
  year: number;
  journal: string;
  pages: string;
  doi: string;
  pmid: string;
  design: string;
  n: number | null;
  population: string;
  endpoint: string;
  hr?: number | null;
  low?: number | null;
  high?: number | null;
  grade: string;
  claim_permitted: string;
  caveat: string;
  mlr: string;
  citation: string;
  url: string;
  status: string;
  directs?: string;
  control_event?: number | null;
  treat_event?: number | null;
  arr?: number | null;
  nnt?: number | null;
  horizon?: string;
  visual_unit?: string;
  spine_means?: string;
  spine_barrier?: string;
  spine_execute?: string;
  spine_measure?: string;
}

export interface CampaignLead {
  statement: string;
  why: string;
  directs: string;
  primaryId?: string;
  citations: { id: string; short: string; pmid?: string; doi?: string; citation: string; claim: string }[];
  doNotClaim: string[];
}

export type TabId = "briefs" | "deck" | "dashboard" | "evidence";
