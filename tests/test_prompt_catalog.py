import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "prompts.json"


class PromptCatalogTests(unittest.TestCase):
    def test_catalog_has_required_sections(self) -> None:
        with CATALOG_PATH.open("r", encoding="utf-8") as handle:
            catalog = json.load(handle)
        for key in ("presets", "templates", "prompts", "settings"):
            self.assertIn(key, catalog)
        self.assertGreaterEqual(len(catalog["presets"]), 1)
        self.assertGreaterEqual(len(catalog["templates"]), 1)
        self.assertEqual(catalog["settings"].get("theme"), "cyberpunk")


if __name__ == "__main__":
    unittest.main()
