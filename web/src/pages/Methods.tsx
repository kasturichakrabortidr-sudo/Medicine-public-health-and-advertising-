export default function Methods() {
  return (
    <article className="methods">
      <div className="eyebrow">Methods</div>
      <h1>How the evidence stays real</h1>
      <h2>Sources</h2>
      <ul>
        <li>Europe PMC (MEDLINE and OA full-text flags) — journals, including paywalled metadata.</li>
        <li>OpenAlex — works, OA status, inverted-index abstracts, UN/NGO institution filters.</li>
        <li>Crossref works search — OA and paywalled bibliographic records; DOI validation gold standard.</li>
        <li>Unpaywall — OA status for records that already have a validated DOI.</li>
        <li>PubMed / MEDLINE via NCBI E-utilities — identifier harvest, abstracts filled from Europe PMC.</li>
        <li>Cochrane / systematic-review strings via Europe PMC and OpenAlex.</li>
        <li>WHO publications API and WHO IRIS — UN health technical packages and reports.</li>
        <li>OpenAlex institutions: WHO and regional offices, PAHO, UNICEF, UNAIDS, UNDP, UNFPA, UNESCO, ILO, UNEP, UNHCR, FAO, WFP, IOM, UNODC, UN Women, UN-Habitat, ITU, UN DESA, World Bank, World Heart Federation.</li>
        <li>Guideline societies via OpenAlex: ESC, AHA, ICMR.</li>
        <li>ClinicalTrials.gov v2 API.</li>
        <li>NICE official guidance URLs when the brief matches (HTTP 200 required), plus WHO HEARTS, WHO NCD fact sheet, WHO Global NCD Action Plan, PAHO HEARTS in the Americas, ESC guideline pages, World Bank NCD brief, and the World Heart Federation heart-failure page.</li>
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
        trial. A GRADE-style table maps study-design markers to certainty bands
        (labelled as heuristic bands, not a full-text GRADE panel).
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
      <h2>Re-running</h2>
      <pre>
        python -m academic_research run --brief examples/brief.example.yaml --out output/research
      </pre>
    </article>
  );
}
