"""Academic literature research automation.

Searches open-access and indexed (including paywalled) journals, national and
international guidelines, UN-system publications, and NGO references. Every
record that survives screening must resolve against a public registry
(Crossref, Europe PMC, ClinicalTrials.gov, or an allow-listed official URL).
Hallucinated citations are structurally impossible: the pipeline never invents
identifiers, titles, or effect sizes.
"""

from .pipeline import ResearchPipeline

__all__ = ["ResearchPipeline"]
__version__ = "1.6.0"
