from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "memos" / "config.yaml"


class DirectWebUILaunchTest(unittest.TestCase):
    def test_launch_is_direct_and_port_is_available_for_agents(self) -> None:
        source = CONFIG.read_text(encoding="utf-8")
        self.assertIn("webui: http://[HOST]:[PORT:5230]", source)
        self.assertIn("  5230/tcp: 5230", source)
        self.assertRegex(source, r"(?m)^ingress: false$")
        self.assertNotRegex(source, r"(?m)^ingress_port:")
        self.assertNotRegex(source, r"(?m)^ingress_stream:")
        self.assertNotRegex(source, r"(?m)^panel_title:")

    def test_packaging_revision_changes_without_changing_image(self) -> None:
        dockerfile = (ROOT / "memos" / "Dockerfile").read_text(encoding="utf-8")
        config = CONFIG.read_text(encoding="utf-8")
        self.assertIn("FROM neosmemo/memos:26.11.0", dockerfile)
        self.assertRegex(config, r'(?m)^version: "26\.11\.0-2"$')

    def test_docs_explain_direct_login_security_boundary(self) -> None:
        docs = (ROOT / "memos" / "DOCS.md").read_text(encoding="utf-8")
        self.assertIn("not HA ingress", docs)
        self.assertIn("Memos handles authentication", docs)
        self.assertIn("Home Assistant single sign-on is not implemented", docs)
