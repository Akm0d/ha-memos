#!/usr/bin/env python3
"""Update the Home Assistant Memos add-on from a verified stable release."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

TAG_PATTERN = re.compile(r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
FROM_PATTERN = re.compile(r"^(FROM neosmemo/memos:)([^\s]+)(.*)$", re.MULTILINE)
WEB_TAG_PATTERN = re.compile(r"^(ARG MEMOS_WEB_TAG=)([^\\s]+)$", re.MULTILINE)


def version_tuple(tag: str) -> tuple[int, int, int]:
    match = TAG_PATTERN.fullmatch(tag)
    if not match:
        raise ValueError(f"Unsupported Memos stable tag: {tag!r}")
    return tuple(int(match.group(p)) for p in ("major", "minor", "patch"))


def add_on_version(tag: str) -> str:
    major, minor, patch = version_tuple(tag)
    return f"{major}.{minor}.{patch}-1"


def _write_if_changed(path: Path, content: str) -> bool:
    if path.read_text(encoding="utf-8") == content:
        return False
    mode = path.stat().st_mode & 0o777
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.chmod(mode)
    temporary_path.replace(path)
    return True


def update_release(dockerfile: Path, config: Path, changelog: Path, tag: str) -> bool:
    target_version = version_tuple(tag)
    docker_text = dockerfile.read_text(encoding="utf-8")
    matches = FROM_PATTERN.findall(docker_text)
    if len(matches) != 1:
        raise ValueError(f"Expected one Memos Docker FROM line, found {len(matches)}")
    current_tag = matches[0][1]
    web_tags = WEB_TAG_PATTERN.findall(docker_text)
    if len(web_tags) != 1 or web_tags[0][1] != current_tag:
        raise ValueError("Pinned Memos frontend source tag must match the runtime image tag")
    current_version = version_tuple(current_tag)
    if target_version < current_version:
        raise ValueError(f"Refusing downgrade from {current_tag} to {tag}")

    # A manual packaging fix may use -2, -3, etc. Never reset it on the
    # same upstream image. The release workflow checks the image tag too.
    if current_version == target_version:
        return False

    release_version = add_on_version(tag)
    config_text = config.read_text(encoding="utf-8")
    config_updated, count = re.subn(
        r'^version: "[^"\n]+"$',
        f'version: "{release_version}"',
        config_text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise ValueError("Expected one quoted version in memos/config.yaml")

    changelog_text = changelog.read_text(encoding="utf-8")
    if not changelog_text.startswith("# Changelog\n"):
        raise ValueError("CHANGELOG.md needs a '# Changelog' heading")
    heading = f"## {release_version}"
    if re.search(rf"^{re.escape(heading)}$", changelog_text, flags=re.MULTILINE):
        raise ValueError(f"Changelog heading already exists: {heading}")

    updated_changelog = (
        f"# Changelog\n\n{heading}\n\n"
        f"- Updated upstream Memos container to stable release {tag}.\n\n"
        + changelog_text[len("# Changelog\n"):].lstrip("\n")
    )
    updated_docker = FROM_PATTERN.sub(
        lambda match: f"{match.group(1)}{tag}{match.group(3)}", docker_text
    )
    updated_docker = WEB_TAG_PATTERN.sub(
        lambda match: f"{match.group(1)}{tag}", updated_docker
    )
    return any((
        _write_if_changed(dockerfile, updated_docker),
        _write_if_changed(config, config_updated),
        _write_if_changed(changelog, updated_changelog),
    ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="Stable upstream tag (e.g. v0.31.0 or 26.11.0)")
    parser.add_argument("--dockerfile", type=Path, default=Path("memos/Dockerfile"))
    parser.add_argument("--config", type=Path, default=Path("memos/config.yaml"))
    parser.add_argument("--changelog", type=Path, default=Path("memos/CHANGELOG.md"))
    args = parser.parse_args()

    try:
        changed = update_release(args.dockerfile, args.config, args.changelog, args.tag)
    except (OSError, ValueError) as error:
        print(f"Memos release update failed: {error}", file=sys.stderr)
        return 1
    print(f"Updated Memos release metadata: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
