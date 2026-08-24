export default function Methods() {
  return (
    <article className="methods">
      <div className="eyebrow">Methods</div>
      <h1>How the evidence stays real</h1>
      <h2>Sources</h2>
      <ul>
        <li>Europe PMC (MEDLINE and OA full-text flags) — journals, including paywalled metadata.</li>
        <li>OpenAlex — works, OA status, inverted-index abstracts, UN/NGO institution filters.</li>
        <li>Crossref — gold-standard DOI validation and bibliographic overwrite.</li>
        <li>WHO publications API and WHO IRIS — UN health technical packages and reports.</li>
        <li>OpenAlex institutions: WHO and regional offices, UNICEF, UNAIDS, UNDP, UNFPA, UNESCO, ILO, UNEP, UNHCR, FAO, WFP, IOM, UNODC, World Bank, World Heart Federation.</li>
        <li>ClinicalTrials.gov v2 API.</li>
        <li>NICE official guidance URLs when the brief matches (HTTP 200 required).</li>
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
        use only regex-parsed HR/OR/RR with 95% CIs.
      </p>
      <h2>Qualitative analysis</h2>
      <p>
        Papers with qualitative method markers undergo narrative review.
        Interpretative phenomenological analysis is applied as a second-order
        coding of experiential language (body, identity, relations, uncertainty,
        constrained agency). Extracts are verbatim abstract clauses — the
        pipeline does not invent interview quotes.
      </p>
      <h2>Re-running</h2>
      <pre>
        python -m academic_research run --brief examples/brief.example.yaml --out output/research
      </pre>
    </article>
  );
}
