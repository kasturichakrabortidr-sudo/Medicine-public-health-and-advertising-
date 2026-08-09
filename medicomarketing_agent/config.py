"""Brief loading and validation for the medicomarketing strategy agent."""

import json
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - yaml is in requirements.txt
    yaml = None

# Fields the pipeline expects. Only `brand` and `therapy_area` are mandatory;
# everything else improves output quality but the phases degrade gracefully,
# recording missing inputs as evidence gaps instead of failing.
REQUIRED_FIELDS = ("brand", "therapy_area")
KNOWN_FIELDS = (
    "brand",
    "product",
    "therapy_area",
    "indication",
    "market",
    "business_goal",
    "target_specialties",
    "hcp_segments",
    "brand_evidence",
    "existing_evidence",
    "evolving_evidence",
    "guidelines",
    "hcp_insights",
    "competitors",
    "access_and_cost",
    "constraints",
    "notes",
)


def load_brief(path: str | Path) -> dict:
    """Load a client brief from a YAML or JSON file and validate it."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML briefs: pip install pyyaml")
        brief = yaml.safe_load(text)
    else:
        brief = json.loads(text)

    if not isinstance(brief, dict):
        raise ValueError(f"Brief in {p} must be a mapping of fields, got {type(brief).__name__}")

    missing = [f for f in REQUIRED_FIELDS if not brief.get(f)]
    if missing:
        raise ValueError(f"Brief is missing required fields: {', '.join(missing)}")
    return brief


def render_brief(brief: dict) -> str:
    """Render the brief as a Markdown document the model can work from."""
    lines = ["# CLIENT BRIEF", ""]
    for key in KNOWN_FIELDS:
        if key not in brief or brief[key] in (None, "", [], {}):
            continue
        lines.append(f"## {key.replace('_', ' ').title()}")
        lines.append(_render_value(brief[key]))
        lines.append("")
    # Preserve any custom fields the user added beyond the known set.
    for key, value in brief.items():
        if key in KNOWN_FIELDS or value in (None, "", [], {}):
            continue
        lines.append(f"## {key.replace('_', ' ').title()}")
        lines.append(_render_value(value))
        lines.append("")
    return "\n".join(lines).strip()


def _render_value(value, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(value, dict):
        return "\n".join(
            f"{pad}- **{k.replace('_', ' ')}**: {_inline_or_block(v, indent)}"
            for k, v in value.items()
        )
    if isinstance(value, list):
        return "\n".join(f"{pad}- {_inline_or_block(item, indent)}" for item in value)
    return f"{pad}{value}"


def _inline_or_block(value, indent: int) -> str:
    if isinstance(value, (dict, list)):
        return "\n" + _render_value(value, indent + 1)
    return str(value)
