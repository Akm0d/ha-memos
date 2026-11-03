from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
ADDON = ROOT / "memos"
CONFIG = ADDON / "config.yaml"


class IngressAndAPIConfigurationTest(unittest.TestCase):
    def test_ingress_and_api_only_ports(self):
        source = CONFIG.read_text(encoding="utf-8")
        self.assertRegex(source, r"(?m)^ingress: true$")
        self.assertRegex(source, r"(?m)^ingress_port: 8099$")
        self.assertIn("  5230/tcp: 5230", source)
        self.assertNotRegex(source, r"(?m)^webui:")
        self.assertIn('panel_title: "Memos"', source)

    def test_admin_and_native_policy_options_are_opt_in(self):
        source = CONFIG.read_text(encoding="utf-8")
        for key in ("admin_username", "admin_password", "admin_password_version", "instance_title", "access_mode", "allow_registration"):
            self.assertIn(key + ":", source)
        self.assertIn('admin_password: "password?"', source)
        self.assertIn("access_mode: unmanaged", source)

    def test_backend_and_ingress_assets_are_isolated(self):
        docker = (ADDON / "Dockerfile").read_text(encoding="utf-8")
        gateway = (ADDON / "ingress" / "main.go").read_text(encoding="utf-8")
        patch = (ADDON / "patch-web.mjs").read_text(encoding="utf-8")
        self.assertIn("FROM neosmemo/memos:26.11.0", docker)
        self.assertIn("ARG MEMOS_WEB_TAG=26.11.0", docker)
        self.assertIn("pnpm exec vite build --mode release --base=./", docker)
        self.assertIn("127.0.0.1", gateway)
        self.assertIn("isSupervisor(r.RemoteAddr)", gateway)
        self.assertIn("isAPIRoute(r.URL.Path)", gateway)
        self.assertIn("createBrowserRouter(routeConfig", patch)
        self.assertIn("baseUrl: window.location.origin,", patch)

    def test_revision_and_immutable_upstream_image(self):
        manifest = CONFIG.read_text(encoding="utf-8")
        self.assertIn('version: "26.11.0-3"', manifest)
        self.assertIn("FROM neosmemo/memos:26.11.0", (ADDON / "Dockerfile").read_text())
