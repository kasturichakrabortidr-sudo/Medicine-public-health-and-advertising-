export default function Methods() {
  return (
    <article className="methods">
      <div className="eyebrow">Methods</div>
      <h1>How the evidence stays real</h1>
      <h2>Sources</h2>
      <ul>
        <li>Europe PMC (MEDLINE and OA full-text flags) — journals, including paywalled metadata.</li>
        <li>OpenAlex — works, OA status, inverted-index abstracts, UN/NGO institution filters, plus a dedicated OA-only harvest.</li>
        <li>Crossref works search — OA and paywalled bibliographic records; DOI validation gold standard.</li>
        <li>Semantic Scholar Graph API — additional OA and paywalled bibliographic hits (retried on a shorter query if the first call is quiet).</li>
        <li>DOAJ — Directory of Open Access Journals article search.</li>
        <li>Unpaywall — OA status for records that already have a validated DOI.</li>
        <li>PubMed / MEDLINE via NCBI E-utilities, including a MeSH-constrained harvest when the brief maps to a known MeSH heading.</li>
        <li>Europe PMC open-access harvest (<code>OPEN_ACCESS:Y</code>) in parallel with mixed OA/paywalled search.</li>
        <li>Cochrane Database of Systematic Reviews via Europe PMC journal filter, plus OpenAlex <code>type:review</code> and an OpenAlex guideline-title harvest.</li>
        <li>Europe PMC preprint index (<code>SRC:PPR</code>) — still dropped unless Crossref/Europe PMC validation succeeds.</li>
        <li>WHO publications API and WHO IRIS — UN health technical packages and reports.</li>
        <li>OpenAlex institutions: WHO and regional offices, PAHO, UNICEF, UNAIDS, UNDP, UNFPA, UNESCO, ILO, UNEP, UNHCR, FAO, WFP, IOM, UNODC, UN Women, UN-Habitat, ITU, UN DESA, World Bank, World Heart Federation.</li>
        <li>Guideline societies via OpenAlex: ESC, AHA, ICMR.</li>
        <li>ClinicalTrials.gov v2 API.</li>
        <li>NICE official guidance URLs when the brief matches (HTTP 200 required), including NG106 and TA388, plus WHO HEARTS, WHO PEN, WHO UHC / primary-care hubs, regional CVD/NCD pages (SEARO, Europe, Africa, EMRO, Western Pacific), WHO hypertension guideline, SDG 3, PAHO HEARTS, ESC guideline pages, World Bank NCD brief, World Heart Federation, UN-branch health pages (UNAIDS, FAO, ILO, UNESCO, WFP, UN-Habitat, UNDRR, UNODC, UNFPA, UN Women, UN DESA, UNICEF NCD, ITU, OHCHR), ACC guideline hub, KDIGO, NHLBI, and India NHM / MoHFW / ICMR / NPCDCS / CSI / CDSCO portals.</li>
      </ul>
      <h2>Inclusion</h2>
      <p>
        A record must be on-topic for the brief and must resolve in a public
        registry. Unresolved DOIs are discarded, not guessed. Paywalled journals
        are included as metadata + abstract only.
      </p>
      <h2>Quantitative analysis</h2>
      <p>
        A transparent claim taxonomy is applied to title+abstract. Frequency is
        the count of unique included records supporting each claim. Forest plots
        use only regex-parsed HR/OR/RR with 95% CIs, one primary estimate per
        trial. A fixed-effect inverse-variance summary and funnel (precision vs
        ln HR) are derived from those same parsed CIs — labelled as a
        transparency calculation, not a de-novo full-text meta-analysis. A GRADE-style table maps study-design markers to certainty bands
        (labelled as heuristic bands, not a full-text GRADE panel). Geography
        tags count unique papers whose title/abstract/issuing body names a
        region; country is never inferred from author affiliation alone.
      </p>
      <h2>Qualitative analysis</h2>
      <p>
        Papers with qualitative method markers undergo narrative review.
        Interpretative phenomenological analysis is applied only to those papers
        as a second-order coding of experiential language (body, identity,
        relations, uncertainty, constrained agency). RCT and guideline abstracts
        are excluded from IPA. Extracts are verbatim abstract clauses — the
        pipeline does not invent interview quotes.
      </p>
      <h2>Exports</h2>
      <p>
        Each Python run writes         <code>literature-deck.json</code>, a numbered
        Markdown reference list, BibTeX, RIS, CSV tables, and
        <code>evidence-campaign-deck.pptx</code> (frequency bars and a forest
        plot drawn only from parsed 95% CIs). The web deck can also download
        BibTeX, RIS, and CSV from the live JSON. A <code>forest-effects.csv</code>
        table lists each parsed CI plus the inverse-variance pooled row.
      </p>
      <h2>Re-running</h2>
      <pre>
        python -m academic_research run --brief examples/brief.example.yaml --out output/research
      </pre>
    </article>
  );
}
