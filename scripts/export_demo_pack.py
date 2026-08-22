"""Write the CardioShield demo pack for the static web fallback."""

from pathlib import Path
import json

from director_api.app import _brief_from_mapping
from director_api.generate import generate_pack
from medicomarketing_agent.config import load_brief

ROOT = Path(__file__).resolve().parent.parent
brief = _brief_from_mapping(load_brief(ROOT / "examples" / "brief.example.yaml"))
pack = generate_pack(brief, mode="demo")
pack["meta"]["source"] = "examples/brief.example.yaml"
out = ROOT / "web" / "public" / "demo.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {out}")
