import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DeckPayload } from "../types";
import { Cite, briefBits, familyLabel } from "./Cite";
import ClaimMatrix from "./ClaimMatrix";
import ForestPlot from "./ForestPlot";
import GradeTable from "./GradeTable";
import IpaCarousel from "./IpaCarousel";
import KeyEvidenceCarousel from "./KeyEvidenceCarousel";
import PrismaFlow from "./PrismaFlow";
import TimeSavings from "./TimeSavings";
import WorkflowInfographic from "./WorkflowInfographic";

const COLORS = ["#e8d5a3", "#7fb9b2", "#b85c38", "#f4efe4", "#4d8f9a", "#c9a227", "#d9c4a3"];

export default function SlideDeck({ deck }: { deck: DeckPayload }) {
  const slides = useMemo(() => buildSlides(deck), [deck]);
  const [i, setI] = useState(0);
  const [printAll, setPrintAll] = useState(false);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "PageDown") setI((n) => Math.min(slides.length - 1, n + 1));
      if (e.key === "ArrowLeft" || e.key === "PageUp") setI((n) => Math.max(0, n - 1));
    };
    const before = () => setPrintAll(true);
    const after = () => setPrintAll(false);
    window.addEventListener("keydown", onKey);
    window.addEventListener("beforeprint", before);
    window.addEventListener("afterprint", after);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("beforeprint", before);
      window.removeEventListener("afterprint", after);
    };
  }, [slides.length]);

  function downloadJson() {
    const blob = new Blob([JSON.stringify(deck, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "literature-deck.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadReferences() {
    const lines = (deck.references || []).map(
      (r) =>
        `[${r.n}] ${r.citation}\n    Validated via ${r.validated_via || "registry"} · ${r.url}`,
    );
    const blob = new Blob([lines.join("\n\n") + "\n"], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "validated-references.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadBibtex() {
    const body = (deck.references || [])
      .map((r) => {
        const key = (r.doi || `ref${r.n}`).replace(/[^A-Za-z0-9]/g, "").slice(0, 40);
        const year = (r.citation.match(/\((\d{4}|n\.d\.)\)/) || [])[1] || "n.d.";
        const lines = [
          `@article{${key},`,
          `  title = {${r.title}},`,
          `  year = {${year}},`,
        ];
        if (r.doi) lines.push(`  doi = {${r.doi}},`);
        if (r.url) lines.push(`  url = {${r.url}},`);
        lines.push(`  note = {Validated via ${r.validated_via || "registry"}},`, "}");
        return lines.join("\n");
      })
      .join("\n\n");
    const blob = new Blob([body + "\n"], { type: "application/x-bibtex" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "validated-references.bib";
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadRis() {
    const body = (deck.references || [])
      .map((r) => {
        const rows = [`TY  - JOUR`, `TI  - ${r.title}`];
        if (r.doi) rows.push(`DO  - ${r.doi}`);
        if (r.url) rows.push(`UR  - ${r.url}`);
        rows.push(`N1  - [${r.n}] Validated via ${r.validated_via || "registry"}`, "ER  - ");
        return rows.join("\n");
      })
      .join("\n\n");
    const blob = new Blob([body + "\n"], { type: "application/x-research-info-systems" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "validated-references.ris";
    a.click();
    URL.revokeObjectURL(url);
  }

  const slide = slides[i];
  return (
    <div className="deck-shell">
      <div className="progress" style={{ width: `${((i + 1) / slides.length) * 100}%` }} />
      <div className="deck-top">
        <a href="/">← Evidence Workflow</a>
        <span>
          {String(i + 1).padStart(2, "0")} / {String(slides.length).padStart(2, "0")} · {slide.title}
        </span>
        <span className="deck-actions">
          <button type="button" onClick={downloadJson}>
            Export JSON
          </button>
          <button type="button" onClick={downloadReferences}>
            Export references
          </button>
          <button type="button" onClick={downloadBibtex}>
            Export BibTeX
          </button>
          <button type="button" onClick={downloadRis}>
            Export RIS
          </button>
          <a className="btn-link" href="/demo/evidence-campaign-deck.pptx" download>
            Download PPTX
          </a>
          <button type="button" onClick={() => window.print()}>
            Print / PDF
          </button>
          <a href="#ref-1">Jump to references</a>
        </span>
      </div>
      {printAll ? (
        slides.map((s) => (
          <section className="slide print-slide" aria-label={s.title} key={s.title}>
            {s.node}
          </section>
        ))
      ) : (
        <section className="slide" aria-label={slide.title}>
          {slide.node}
        </section>
      )}
      <div className="deck-nav">
        <button type="button" onClick={() => setI(0)}>Start</button>
        <button type="button" onClick={() => setI((n) => Math.max(0, n - 1))}>Prev slide</button>
        <button type="button" className="deck-next" onClick={() => setI((n) => Math.min(slides.length - 1, n + 1))}>
          Next slide
        </button>
        <button type="button" onClick={() => setI(slides.length - 1)}>Refs</button>
      </div>
    </div>
  );
}

function buildSlides(deck: DeckPayload) {
  const b = briefBits(deck);
  const ts = deck.meta.time_savings;
  const familyData = deck.quantitative.by_source_family.map((d) => ({
    name: familyLabel(d.id),
    value: d.count,
  }));
  const claimData = deck.quantitative.claim_frequency.map((c) => ({
    name: c.label,
    percent: c.percent,
    count: c.count,
  }));
  const yearData = deck.quantitative.by_year;
  const oa = deck.quantitative.oa_vs_paywalled;
  const designData = (deck.quantitative.by_study_design || []).map((d) => ({
    name: d.label,
    value: d.count,
  }));
  const gradeRows = deck.quantitative.grade_profile || [];
  const agencyData = (deck.quantitative.agency_coverage || []).map((d) => ({
    name: d.body,
    count: d.count,
  }));
  const geoData = (deck.quantitative.geography || []).map((d) => ({
    name: d.id,
    count: d.count,
    percent: d.percent,
  }));
  const yieldData = (deck.quantitative.connector_yield || [])
    .filter((d) => d.hits > 0 || !d.ok)
    .slice(0, 14)
    .map((d) => ({
      name: d.connector,
      hits: d.hits,
    }));

  return [
    {
      title: "Title",
      node: (
        <>
          <div className="eyebrow">Literature review & analysis deck</div>
          <h1>
            {b.brand}: validated evidence for {b.indication || b.therapy}
          </h1>
          <p className="lede" style={{ color: "#d7e4e1" }}>
            A visual workflow from multi-source search to frequency analysis, IPA
            themes, and numbered real citations. Generated {deck.meta.generated_at}.
          </p>
          <div className="kpi-row">
            <div className="kpi">
              <strong>{deck.prisma.included}</strong>validated records
            </div>
            <div className="kpi">
              <strong>{deck.references.length}</strong>numbered citations
            </div>
            <div className="kpi">
              <strong>{ts.reduction_percent}%</strong>time reduction vs 40-hour review
            </div>
            <div className="kpi">
              <strong>{deck.qualitative.ipa.superordinate_themes.length}</strong>IPA themes
            </div>
          </div>
        </>
      ),
    },
    {
      title: "Brief & PICO",
      node: (
        <>
          <h2>01 · Brief and research question</h2>
          <p>{deck.pico.question}</p>
          <table className="table">
            <tbody>
              <tr><th>Population</th><td>{deck.pico.population}</td></tr>
              <tr><th>Intervention</th><td>{deck.pico.intervention}</td></tr>
              <tr><th>Comparator</th><td>{deck.pico.comparator}</td></tr>
              <tr><th>Outcomes</th><td>{deck.pico.outcomes}</td></tr>
              <tr><th>Setting</th><td>{deck.pico.setting}</td></tr>
            </tbody>
          </table>
        </>
      ),
    },
    {
      title: "Workflow",
      node: (
        <>
          <h2>02 · The time-saving workflow</h2>
          <p>
            Manual narrative reviews commonly consume ~{ts.manual_baseline_hours} hours
            of sequential search, sifting, and slide-making. This run is designed
            to land near ~{ts.automated_hours} hours of analyst oversight
            ({ts.reduction_percent}% reduction). {ts.how}
          </p>
          <WorkflowInfographic />
          <p className="muted-note">
            Search streams this run: {deck.search.queries.map((q) => q.id).join(" · ")}
          </p>
        </>
      ),
    },
    {
      title: "Time savings",
      node: (
        <>
          <h2>03 · Calendar time vs this run</h2>
          <p>
            A typical sequential hand search, screening, reference-checking and
            slide build is modelled at {ts.manual_baseline_hours} analyst hours.
            This workflow targets ~{ts.automated_hours} hours of oversight
            ({ts.reduction_percent}% reduction, above the 50% brief). {ts.how}
          </p>
          <TimeSavings
            manualHours={ts.manual_baseline_hours}
            automatedHours={ts.automated_hours}
            reduction={ts.reduction_percent}
            wallClockSeconds={ts.wall_clock_seconds}
          />
        </>
      ),
    },
    {
      title: "Sources",
      node: (
        <>
          <h2>04 · Where we looked</h2>
          <p>
            Open-access and paywalled indexed journals (Europe PMC, OpenAlex,
            Crossref, PubMed/MEDLINE, Semantic Scholar, Unpaywall OA flags),
            Cochrane Database records, DOAJ, preprint indexes, national and
            international guidelines (ESC, AHA, NICE, ICMR / NPCDCS when
            retrieved), WHO IRIS, WHO publications, UN-system institutions on
            OpenAlex (WHO, PAHO, UNICEF, UNAIDS, UNDP, UNFPA, UNESCO, ILO, UNEP,
            UNHCR, FAO, WFP, IOM, UNODC, UN Women, UN-Habitat, ITU, UN DESA,
            World Bank), NGOs, and ClinicalTrials.gov. Official URL seeds add
            WHO regional CVD/NCD pages, SDG 3, UN-branch health pages, and India
            ministry / ICMR portals when the brief matches. Paywalled papers
            contribute title/abstract/DOI only — full text is never scraped.
          </p>
          <div className="chart-panel" style={{ height: 340 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={familyData} dataKey="value" nameKey="name" outerRadius={120} label>
                  {familyData.map((_, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </>
      ),
    },
    {
      title: "Harvest yield",
      node: (
        <>
          <h2>05 · Connector harvest (live APIs this run)</h2>
          <p>
            Hits returned before de-duplication and validation. Quiet APIs
            (zero hits) are kept in the JSON; only positive or failed
            connectors are plotted.
          </p>
          {yieldData.length ? (
            <div className="chart-panel" style={{ height: 380 }}>
              <ResponsiveContainer>
                <BarChart data={yieldData} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis type="number" stroke="#d7e4e1" />
                  <YAxis type="category" dataKey="name" width={180} stroke="#d7e4e1" />
                  <Tooltip />
                  <Bar dataKey="hits" fill="#7fb9b2" name="raw hits" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p>Connector yield was not recorded for this corpus.</p>
          )}
        </>
      ),
    },
    {
      title: "PRISMA",
      node: (
        <>
          <h2>06 · Screening flow</h2>
          <PrismaFlow prisma={deck.prisma} />
        </>
      ),
    },
    {
      title: "Validation",
      node: (
        <>
          <h2>07 · Anti-hallucination contract</h2>
          <p>{deck.meta.validation_policy}</p>
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Provenance</th>
                <th>Identifier</th>
                <th>OA</th>
              </tr>
            </thead>
            <tbody>
              {deck.references.slice(0, 8).map((r) => (
                <tr key={r.n}>
                  <td>{r.n}</td>
                  <td>{r.validated_via}</td>
                  <td>{r.doi || r.pmid || r.url}</td>
                  <td>{r.is_oa ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>…{Math.max(deck.references.length - 8, 0)} further validated items in the reference list.</p>
        </>
      ),
    },
    {
      title: "Frequency",
      node: (
        <>
          <h2>08 · Quantitative frequency analysis</h2>
          <p>
            Commonality of supporting facts across the included corpus (unique
            papers per coded claim ÷ included n = {deck.quantitative.n_included}).
          </p>
          <div className="chart-panel" style={{ height: 380 }}>
            <ResponsiveContainer>
              <BarChart data={claimData} layout="vertical" margin={{ left: 24, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis type="number" stroke="#d7e4e1" />
                <YAxis type="category" dataKey="name" width={210} stroke="#d7e4e1" />
                <Tooltip />
                <Bar dataKey="percent" fill="#e8d5a3" name="% of corpus" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      ),
    },
    {
      title: "Claim table",
      node: (
        <>
          <h2>09 · Supporting-fact table with citations</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Claim</th>
                <th>n</th>
                <th>%</th>
                <th>Citations</th>
              </tr>
            </thead>
            <tbody>
              {deck.quantitative.claim_frequency.map((c) => (
                <tr key={c.id}>
                  <td>{c.label}</td>
                  <td>{c.count}</td>
                  <td>{c.percent}</td>
                  <td>
                    <Cite n={c.citation_ids} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ),
    },
    {
      title: "Heatmap",
      node: (
        <>
          <h2>10 · Claim × source infographic</h2>
          <p>
            How often each supporting fact appears inside each source family.
            Cells are counts of unique validated papers — not modelled weights.
          </p>
          <ClaimMatrix claims={deck.quantitative.claim_frequency} records={deck.records} />
        </>
      ),
    },
    {
      title: "Time series",
      node: (
        <>
          <h2>11 · Publication years, access, and study design</h2>
          <div className="grid-2" style={{ padding: 0 }}>
            <div className="chart-panel" style={{ height: 280 }}>
              <ResponsiveContainer>
                <BarChart data={yearData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="year" stroke="#d7e4e1" />
                  <YAxis stroke="#d7e4e1" />
                  <Tooltip />
                  <Bar dataKey="count" fill="#7fb9b2" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-panel" style={{ height: 280 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={[
                      { name: "Open access", value: oa.open_access },
                      { name: "Paywalled / abstract-only", value: oa.paywalled_or_unclear },
                    ]}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={100}
                    label
                  >
                    <Cell fill="#7fb9b2" />
                    <Cell fill="#b85c38" />
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          {designData.length ? (
            <div className="chart-panel" style={{ height: 260, marginTop: "1rem" }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={designData} dataKey="value" nameKey="name" outerRadius={90} label>
                    {designData.map((_, idx) => (
                      <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : null}
        </>
      ),
    },
    {
      title: "Forest",
      node: (
        <>
          <h2>12 · Forest plot of parsed effect sizes</h2>
          <ForestPlot rows={deck.forest} />
        </>
      ),
    },
    {
      title: "GRADE bands",
      node: (
        <>
          <h2>13 · Evidence-certainty table (design bands)</h2>
          <p>
            Transparent design labels from title/abstract markers, mapped to
            GRADE-style certainty bands. This is not a full-text GRADE panel:
            risk of bias is not re-scored here. Effect sizes still appear only
            when a 95% CI was parsed from a validated abstract.
          </p>
          <GradeTable rows={gradeRows} />
        </>
      ),
    },
    {
      title: "Pivotal cards",
      node: (
        <>
          <h2>14 · Pivotal trials and guidelines carousel</h2>
          <p>
            Flip through the highest-signal validated records — pivotal outcome
            trials first, then guidelines. Each card is numbered for the
            reference list.
          </p>
          <KeyEvidenceCarousel
            records={[
              ...deck.records.filter((r) => r.effects.length),
              ...deck.guidelines,
            ].filter((r, idx, arr) => arr.findIndex((x) => x.citation_id === r.citation_id) === idx)}
          />
        </>
      ),
    },
    {
      title: "Guidelines",
      node: (
        <>
          <h2>15 · International and national guidelines</h2>
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Title</th>
                <th>Body</th>
                <th>Year</th>
              </tr>
            </thead>
            <tbody>
              {deck.guidelines.slice(0, 10).map((g) => (
                <tr key={g.citation_id}>
                  <td>
                    <Cite n={g.citation_id} />
                  </td>
                  <td>{g.title}</td>
                  <td>{g.issuing_body}</td>
                  <td>{g.year}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {deck.guidelines.length === 0 ? <p>No guideline-classified records survived validation.</p> : null}
        </>
      ),
    },
    {
      title: "UN / NGO",
      node: (
        <>
          <h2>16 · UN branches and non-profit references</h2>
          <p>
            WHO (headquarters and regional offices), UNICEF, UNAIDS, UNDP, UNFPA,
            UNESCO, ILO, UNEP, UNHCR, FAO, WFP, IOM, UNODC, UN Women, UN-Habitat,
            ITU, UN DESA, World Bank, and the World Heart Federation were queried
            via OpenAlex institution filters plus WHO IRIS / publications APIs.
            Official URL seeds (HTTP 200) this run also include WHO HEARTS, WHO
            regional CVD/NCD pages (SEARO, Europe, Africa), SDG 3, UN-branch
            health pages (UNAIDS, FAO, ILO, UNESCO, WFP, UN-Habitat, UNDRR,
            UNODC), the WHO hypertension guideline, PAHO HEARTS, the World Bank
            NCD brief, and India NHM / MoHFW / ICMR / NPCDCS portals when the
            market matches.
          </p>
          {agencyData.length ? (
            <div className="chart-panel" style={{ height: 240, marginBottom: "1rem" }}>
              <ResponsiveContainer>
                <BarChart data={agencyData} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis type="number" stroke="#d7e4e1" />
                  <YAxis type="category" dataKey="name" width={220} stroke="#d7e4e1" />
                  <Tooltip />
                  <Bar dataKey="count" fill="#c9a227" name="validated records" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : null}
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Title</th>
                <th>Issuing body</th>
              </tr>
            </thead>
            <tbody>
              {deck.un_and_ngo.slice(0, 10).map((g) => (
                <tr key={g.citation_id}>
                  <td>
                    <Cite n={g.citation_id} />
                  </td>
                  <td>{g.title}</td>
                  <td>{g.issuing_body}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ),
    },
    {
      title: "Geography",
      node: (
        <>
          <h2>17 · Where the included evidence sits</h2>
          <p>
            Region tags are taken from title, abstract, and issuing body
            (India, Africa, SEARO, PAHO, Europe, North America, UN-system,
            or multi-country). No country is inferred from author affiliation
            alone.
          </p>
          {geoData.length ? (
            <div className="chart-panel" style={{ height: 360 }}>
              <ResponsiveContainer>
                <BarChart data={geoData} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis type="number" stroke="#d7e4e1" />
                  <YAxis type="category" dataKey="name" width={220} stroke="#d7e4e1" />
                  <Tooltip />
                  <Bar dataKey="count" fill="#e8d5a3" name="validated records" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p>No geography tags were assigned in this corpus.</p>
          )}
        </>
      ),
    },
    {
      title: "Narrative",
      node: (
        <>
          <h2>18 · Narrative review</h2>
          <p>{deck.qualitative.narrative_review.summary}</p>
          <ul>
            {deck.qualitative.narrative_review.points.slice(0, 6).map((p) => (
              <li key={p.citation_id}>
                {p.point} <Cite n={p.citation_id} />
              </li>
            ))}
          </ul>
        </>
      ),
    },
    {
      title: "IPA",
      node: (
        <>
          <h2>19 · IPA theme carousel</h2>
          <p>{deck.qualitative.method_note}</p>
          <IpaCarousel themes={deck.qualitative.ipa.superordinate_themes} />
        </>
      ),
    },
    {
      title: "Cohort insights",
      node: (
        <>
          <h2>20 · Insights for {deck.insights.cohort}</h2>
          <div className="grid-2" style={{ padding: 0 }}>
            <div>
              <h3>Prevalent benefits / supporting facts</h3>
              <ul>
                {deck.insights.prevalent_benefits.map((c) => (
                  <li key={c.id}>
                    {c.label} ({c.percent}%) <Cite n={c.citation_ids} />
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Prevalent barriers</h3>
              <ul>
                {deck.insights.prevalent_barriers.map((c) => (
                  <li key={c.id}>
                    {c.label} ({c.percent}%) <Cite n={c.citation_ids} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      ),
    },
    {
      title: "Novel angles",
      node: (
        <>
          <h2>21 · Novel angles and evidence gaps</h2>
          <h3>What this corpus newly clarifies for campaign design</h3>
          <ul>
            {deck.insights.novel_angles.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
          <h3>Gaps (honest)</h3>
          <ul>
            {(deck.insights.gaps.length ? deck.insights.gaps : ["No structural gaps flagged in this run."]).map(
              (x) => (
                <li key={x}>{x}</li>
              ),
            )}
          </ul>
        </>
      ),
    },
    {
      title: "Use in a campaign deck",
      node: (
        <>
          <h2>22 · Ready to drop into a campaign evidence section</h2>
          <ol>
            <li>Lead with the PRISMA counts and the validation contract.</li>
            <li>Show the frequency bars as “what the literature repeatedly supports”.</li>
            <li>Place the forest plot beside guideline Class/level language.</li>
            <li>Use IPA themes to brief creative and medical on patient/HCP meaning — not slogans.</li>
            <li>Keep the numbered reference list attached; every claim chip traces to a URL/DOI.</li>
          </ol>
          <p>
            Product: {b.product || "—"}. Market: {b.market || "international"}. Corpus n=
            {deck.prisma.included}.
          </p>
        </>
      ),
    },
    {
      title: "References",
      node: (
        <>
          <h2 id="ref-1">23 · Numbered, registry-validated references</h2>
          <div className="ref-list">
            {deck.references.map((r) => (
              <p key={r.n} id={`ref-${r.n}`}>
                <b>[{r.n}]</b> {r.citation}{" "}
                <a href={r.url} target="_blank" rel="noreferrer">
                  source
                </a>
                . Validated via {r.validated_via}.
              </p>
            ))}
          </div>
        </>
      ),
    },
  ];
}
