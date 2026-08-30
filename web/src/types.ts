export type SourceFamily =
  | "open_access"
  | "paywalled_journal"
  | "international_guideline"
  | "national_guideline"
  | "un_agency"
  | "ngo"
  | "trial_registry";

export interface Validation {
  status: string;
  via: string;
  identifier: string;
  retrieved_at: string;
  canonical_url: string;
}

export interface EffectSize {
  metric: string;
  value: number;
  ci_low: number;
  ci_high: number;
  outcome: string;
  excerpt: string;
}

export interface EvidenceRecord {
  key: string;
  title: string;
  url: string;
  source_connector: string;
  source_family: SourceFamily | string;
  issuing_body: string;
  doi?: string | null;
  pmid?: string | null;
  nct_id?: string | null;
  authors: string[];
  year?: number | null;
  venue?: string | null;
  is_oa: boolean;
  abstract: string;
  validation?: Validation | null;
  claims: string[];
  effects: EffectSize[];
  is_qualitative: boolean;
  is_guideline: boolean;
  study_design?: string;
  snippets: string[];
  citation_id: number;
}

export interface ClaimFreq {
  id: string;
  label: string;
  count: number;
  percent: number;
  citation_ids: number[];
}

export interface ForestRow {
  citation_id: number;
  label: string;
  year?: number | null;
  metric: string;
  value: number;
  ci_low: number;
  ci_high: number;
  outcome: string;
  excerpt: string;
  doi?: string | null;
}

export interface IpaTheme {
  id: string;
  title: string;
  description: string;
  n_papers: number;
  citation_ids: number[];
  evidence_extracts: { citation_id: number; text: string }[];
  analytic_memo: string;
}

export interface Reference {
  n: number;
  citation: string;
  title: string;
  url: string;
  doi?: string | null;
  pmid?: string | null;
  source_family: string;
  is_oa: boolean;
  validated_via?: string | null;
  validated_at?: string | null;
}

export interface DeckPayload {
  meta: {
    generated_at: string;
    pipeline_version: string;
    validation_policy: string;
    time_savings: {
      claim: string;
      manual_baseline_hours: number;
      automated_hours: number;
      reduction_percent: number;
      how: string;
      wall_clock_seconds?: number;
    };
  };
  brief: Record<string, unknown>;
  pico: {
    population: string;
    intervention: string;
    comparator: string;
    outcomes: string;
    setting: string;
    question: string;
  };
  search: { queries: { id: string; purpose: string }[]; log: { step: string; detail: string }[] };
  prisma: {
    identified: number;
    duplicates_removed: number;
    screened: number;
    excluded_off_topic: number;
    excluded_unvalidated: number;
    included: number;
  };
  records: EvidenceRecord[];
  quantitative: {
    n_included: number;
    claim_frequency: ClaimFreq[];
    by_source_family: { id: string; count: number; percent: number }[];
    by_study_design?: { id: string; label: string; count: number; percent: number }[];
    grade_profile?: {
      id: string;
      label: string;
      band: string;
      note: string;
      count: number;
      citation_ids: number[];
    }[];
    by_year: { year: number; count: number }[];
    oa_vs_paywalled: { open_access: number; paywalled_or_unclear: number };
    agency_coverage?: { body: string; count: number }[];
  };
  qualitative: {
    method_note: string;
    n_qualitative_papers: number;
    narrative_review: {
      summary: string;
      points: { citation_id: number; title: string; point: string }[];
    };
    ipa: { superordinate_themes: IpaTheme[] };
  };
  forest: ForestRow[];
  guidelines: EvidenceRecord[];
  un_and_ngo: EvidenceRecord[];
  insights: {
    cohort: string;
    prevalent_supporting_facts: ClaimFreq[];
    prevalent_benefits: ClaimFreq[];
    prevalent_barriers: ClaimFreq[];
    novel_angles: string[];
    gaps: string[];
  };
  references: Reference[];
}
