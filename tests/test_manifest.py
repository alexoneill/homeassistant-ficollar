"""Test integration manifests and JSON structures."""

import json
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).parent.parent
CUSTOM_COMPONENTS = REPO_ROOT / "custom_components" / "ficollar"


class TestManifests(unittest.TestCase):
    """Test integration manifest and metadata files."""

    def test_hacs_json(self) -> None:
        """Verify hacs.json structure and contents."""
        hacs_path = REPO_ROOT / "hacs.json"
        self.assertTrue(hacs_path.exists(), "hacs.json must exist in root")

        with open(hacs_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("name", data)
        self.assertEqual(data["name"], "Fi Collar")
        self.assertIn("homeassistant", data)

    def test_manifest_json(self) -> None:
        """Verify custom component manifest.json."""
        manifest_path = CUSTOM_COMPONENTS / "manifest.json"
        self.assertTrue(manifest_path.exists(), "manifest.json must exist in custom_components/ficollar")

        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)

        required_keys = [
            "domain",
            "name",
            "codeowners",
            "config_flow",
            "documentation",
            "integration_type",
            "iot_class",
            "issue_tracker",
            "requirements",
            "version",
        ]
        for key in required_keys:
            self.assertIn(key, data, f"manifest.json missing required key: {key}")

        self.assertEqual(data["domain"], "ficollar")
        self.assertEqual(data["name"], "Fi Collar")
        self.assertTrue(data["config_flow"])
        self.assertEqual(data["integration_type"], "hub")
        self.assertIn("pyficollar>=0.1.3", data["requirements"])

    def test_strings_and_translations_match(self) -> None:
        """Verify strings.json matches translations/en.json."""
        strings_path = CUSTOM_COMPONENTS / "strings.json"
        translations_path = CUSTOM_COMPONENTS / "translations" / "en.json"

        self.assertTrue(strings_path.exists(), "strings.json must exist")
        self.assertTrue(translations_path.exists(), "translations/en.json must exist")

        with open(strings_path, encoding="utf-8") as f:
            strings_data = json.load(f)

        with open(translations_path, encoding="utf-8") as f:
            trans_data = json.load(f)

        self.assertEqual(strings_data, trans_data, "strings.json and translations/en.json must match")

    def test_brand_assets_exist(self) -> None:
        """Verify brand assets exist for both light and dark modes."""
        for folder in [REPO_ROOT / "brand", CUSTOM_COMPONENTS / "brand"]:
            for filename in ["icon.png", "icon@2x.png", "dark_icon.png", "dark_icon@2x.png", "logo.png", "dark_logo.png"]:
                asset_path = folder / filename
                self.assertTrue(asset_path.exists(), f"{asset_path} must exist")
                self.assertGreater(asset_path.stat().st_size, 0, f"{asset_path} must not be empty")


if __name__ == "__main__":
    unittest.main()
