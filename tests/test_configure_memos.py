from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "memos" / "configure-memos.py"
SPEC = importlib.util.spec_from_file_location("configure_memos", SCRIPT)
assert SPEC and SPEC.loader
config = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(config)


class MemosHomeAssistantConfigurationTest(unittest.TestCase):
    def test_default_is_unmanaged_and_preserves_existing_users(self):
        document, known, password = config.render({}, set())
        self.assertEqual(document, {})
        self.assertEqual(known, set())
        self.assertIsNone(password)

    def test_bootstraps_admin_with_file_secret_and_version(self):
        document, known, password = config.render({
            "admin_username": "admin",
            "admin_password": "example-secret",
            "admin_password_version": 3,
        }, set())
        self.assertEqual(password, "example-secret")
        self.assertEqual(document["users"][0]["name"], "users/admin")
        self.assertEqual(document["users"][0]["role"], "ADMIN")
        self.assertTrue(document["users"][0]["password"].startswith("$" + "{file:"))
        self.assertNotIn("example-secret", str(document))
        self.assertEqual(document["lifecycle"][0]["writeOnlyVersion"], 3)
        self.assertIn("users/admin", known)

    def test_optional_access_and_general_settings_are_declared(self):
        document, _, _ = config.render({
            "access_mode": "private",
            "instance_title": "Memos on Hearth",
            "allow_registration": "deny",
        }, set())
        settings = {s["name"]: s for s in document["instanceSettings"]}
        self.assertEqual(
            settings["instance/settings/ACCESS"]["accessSetting"]["accessMode"],
            "INSTANCE_ACCESS_MODE_PRIVATE",
        )
        general = settings["instance/settings/GENERAL"]["generalSetting"]
        self.assertEqual(general["customProfile"]["title"], "Memos on Hearth")
        self.assertTrue(general["disallowUserRegistration"])
        self.assertIn("generalSetting.additionalStyle", document["lifecycle"][0]["ignoreChanges"])

    def test_unmanaged_releases_previous_configuration_without_deleting_database_values(self):
        known = {"instance/settings/GENERAL", "instance/settings/ACCESS", "users/admin"}
        document, still_known, _ = config.render({}, known)
        self.assertEqual(still_known, known)
        self.assertEqual(
            document["removed"],
            [{"resource": name, "destroy": False} for name in sorted(known)],
        )

    def test_password_username_pairs_are_required_and_secret_is_never_echoed(self):
        for opts in ({"admin_username": "admin"}, {"admin_password": "secret"}):
            with self.subTest(opts=opts), self.assertRaisesRegex(ValueError, "both"):
                config.render(opts, set())

    def test_rejects_invalid_username_and_version(self):
        with self.assertRaisesRegex(ValueError, "valid Memos username"):
            config.render({"admin_username": "name/invalid", "admin_password": "secret"}, set())
        with self.assertRaisesRegex(ValueError, "positive integer"):
            config.render({"admin_password_version": 0}, set())

    def test_password_rotation_is_explicit_not_automatic(self):
        first, _, _ = config.render({"admin_username": "admin", "admin_password": "one"}, set())
        second, _, _ = config.render({"admin_username": "admin", "admin_password": "two"}, set())
        self.assertEqual(first["lifecycle"], second["lifecycle"])
