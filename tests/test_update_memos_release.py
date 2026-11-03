from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "update_memos_release.py"
SPEC = importlib.util.spec_from_file_location("update_memos_release", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


class MemosReleaseUpdaterTest(unittest.TestCase):
    def make_files(self, root: Path, upstream_tag: str, addon_version: str):
        docker = root / "Dockerfile"
        config = root / "config.yaml"
        changelog = root / "CHANGELOG.md"
        docker.write_text(
            f"FROM neosmemo/memos:{upstream_tag}\n"
            "ENV MEMOS_DATA=/data\n",
            encoding="utf-8",
        )
        config.write_text(
            f'name: "Memos"\nversion: "{addon_version}"\n',
            encoding="utf-8",
        )
        changelog.write_text(
            f"# Changelog\n\n## {addon_version}\n\n- Packaging fix.\n",
            encoding="utf-8",
        )
        return docker, config, changelog

    def test_formats(self):
        self.assertEqual(updater.add_on_version("26.11.0"), "26.11.0-1")
        self.assertEqual(updater.add_on_version("v0.31.0"), "0.31.0-1")
        self.assertEqual(updater.add_on_version("26.11.2"), "26.11.2-1")

    def test_updates_docker_manifest_changelog_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            docker, config, changelog = self.make_files(
                Path(folder), "26.11.0", "26.11.0-3"
            )
            self.assertTrue(updater.update_release(docker, config, changelog, "26.11.1"))
            self.assertIn("FROM neosmemo/memos:26.11.1", docker.read_text())
            self.assertIn('version: "26.11.1-1"', config.read_text())
            self.assertIn("## 26.11.1-1", changelog.read_text())
            self.assertFalse(updater.update_release(docker, config, changelog, "26.11.1"))
            self.assertEqual(changelog.read_text().count("## 26.11.1-1"), 1)

    def test_same_image_preserves_packaging_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            docker, config, changelog = self.make_files(
                Path(folder), "26.11.0", "26.11.0-4"
            )
            self.assertFalse(updater.update_release(docker, config, changelog, "26.11.0"))
            self.assertIn('version: "26.11.0-4"', config.read_text())

    def test_rejects_downgrades(self):
        with tempfile.TemporaryDirectory() as folder:
            files = self.make_files(Path(folder), "26.11.0", "26.11.0-1")
            with self.assertRaisesRegex(ValueError, "Refusing downgrade"):
                updater.update_release(*files, "v0.31.0")

    def test_rejects_nonstable_tags(self):
        for tag in ("26.11.0-rc.1", "canary", "stable", "latest", "26.11"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "Unsupported"):
                updater.version_tuple(tag)

    def test_legacy_tag_transition(self):
        with tempfile.TemporaryDirectory() as folder:
            files = self.make_files(Path(folder), "v0.31.0", "0.31.0-2")
            self.assertTrue(updater.update_release(*files, "26.11.0"))
            self.assertIn('version: "26.11.0-1"', files[1].read_text())

    def test_repository_metadata_matches_image_and_fork(self):
        docker = (ROOT / "memos" / "Dockerfile").read_text(encoding="utf-8")
        config = (ROOT / "memos" / "config.yaml").read_text(encoding="utf-8")
        repository = (ROOT / "repository.json").read_text(encoding="utf-8")
        image_tags = updater.FROM_PATTERN.findall(docker)
        self.assertEqual(len(image_tags), 1)
        self.assertIn(
            f'version: "{updater.add_on_version(image_tags[0][1])}"',
            config,
        )
        self.assertIn("github.com/Akm0d/ha-memos", repository)
        self.assertIn("github.com/Akm0d/ha-memos", config)
