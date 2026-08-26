import { Link } from "react-router-dom";

export default function Home() {
  return (
    <>
      <header className="hero">
        <div className="eyebrow">Academic research automation</div>
        <h1>From brief to a citation-numbered visual evidence deck, in one workflow.</h1>
        <p className="lede">
          Search open-access and indexed journals, national and international
          guidelines, UN-system publications, NGO references, and trial
          registries. Keep only identifiers that resolve. Then run frequency
          analysis and IPA-informed qualitative synthesis — and present it as
          charts, forest plots, and a carousel you can drop into a campaign deck.
        </p>
        <p>
          <Link className="btn" to="/deck">
            Open the CardioShield evidence deck
          </Link>{" "}
          <Link className="btn ghost" to="/run">
            Run a new brief
          </Link>
        </p>
      </header>

      <section className="workflow" aria-label="Seven-step workflow">
        {[
          ["01 Search", "Europe PMC, OpenAlex, Crossref, PubMed, WHO IRIS, UN institutions, ClinicalTrials.gov"],
          ["02 Screen", "On-topic filter from the brief; PRISMA-style counts"],
          ["03 Validate", "DOI / PMID / NCT / official URL must resolve or the record is dropped"],
          ["04 Collate", "Abstracts coded to a claim taxonomy tied to PICO"],
          ["05 Quant", "Frequency of supporting facts; forest plot of parsed CIs"],
          ["06 Qual", "Narrative review + IPA superordinate themes"],
          ["07 Deck", "Visual slides with numbered real citations"],
        ].map(([t, d]) => (
          <div className="step" key={t}>
            <b>{t}</b>
            {d}
          </div>
        ))}
      </section>

      <section className="grid-3">
        <article className="card">
          <h3>≥50% less calendar time</h3>
          <p>
            A typical hand search + screening + slide build is modelled at 40
            analyst hours. This workflow targets ~12 hours of oversight (70%
            reduction) by parallelising search, rejecting fake citations, and
            auto-drawing the deck.
          </p>
        </article>
        <article className="card">
          <h3>No invented references</h3>
          <p>
            Titles, authors, and years are overwritten from Crossref / Europe PMC
            / ClinicalTrials.gov / WHO. Effect sizes appear only when a 95% CI is
            parsed from the abstract text.
          </p>
        </article>
        <article className="card">
          <h3>Built for medicomarketing evidence sections</h3>
          <p>
            The same CardioShield brief used by the medicomarketing agent is the
            live demo: HFrEF, sacubitril/valsartan, ESC/ACC/NICE, WHO HEARTS, and
            lived-experience literature.
          </p>
        </article>
      </section>
      <p className="footer">
        Draft evidence only. Medical claims still require organisational MLR
        review before use with healthcare professionals.
      </p>
    </>
  );
}
