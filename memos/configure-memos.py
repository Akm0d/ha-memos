#!/usr/bin/env python3
"""Compile optional Home Assistant options into Memos' native 26.10+ config.

No HA option is managed by default. Historical resource names are retained so
unsetting an option explicitly releases previously managed Memos resources.
Never print secrets; the generated JSON references a transient password file.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

OPTIONS = Path(os.getenv("MEMOS_HA_OPTIONS", "/data/options.json"))
CONFIG_DIR = Path(os.getenv("MEMOS_HA_CONFIG_DIR", "/etc/memos/config"))
KNOWN = Path(os.getenv("MEMOS_HA_KNOWN", "/data/ha-memos-managed.json"))
PASSWORD_FILE = Path(os.getenv("MEMOS_HA_PASSWORD_FILE", "/run/memos-admin-password"))
USERNAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,34}[A-Za-z0-9])?$")


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, content: object, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(content, output, indent=2)
            output.write("\n")
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def render(options: dict, historical: set[str]) -> tuple[dict, set[str], str | None]:
    name = options.get("admin_username") or ""
    password = options.get("admin_password") or ""
    title = options.get("instance_title") or ""
    mode = options.get("access_mode", "unmanaged")
    registration = options.get("allow_registration", "unmanaged")
    version = options.get("admin_password_version", 1)

    if not isinstance(name, str) or (name and not USERNAME.fullmatch(name)):
        raise ValueError("admin_username must be a valid Memos username")
    if not isinstance(password, str) or (bool(name) != bool(password)):
        raise ValueError("admin_username and admin_password must both be set or both be empty")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError("admin_password_version must be a positive integer")
    if not isinstance(title, str) or len(title) > 160:
        raise ValueError("instance_title must be at most 160 characters")
    if mode not in ("unmanaged", "private", "public"):
        raise ValueError("access_mode must be unmanaged, private or public")
    if registration not in ("unmanaged", "allow", "deny"):
        raise ValueError("allow_registration must be unmanaged, allow or deny")

    desired: set[str] = set()
    settings: list[dict] = []
    users: list[dict] = []
    lifecycle: list[dict] = []

    if mode != "unmanaged":
        desired.add("instance/settings/ACCESS")
        settings.append({
            "name": "instance/settings/ACCESS",
            "accessSetting": {"accessMode": "INSTANCE_ACCESS_MODE_" + mode.upper()},
        })

    if title or registration != "unmanaged":
        desired.add("instance/settings/GENERAL")
        general: dict = {}
        if title:
            general["customProfile"] = {"title": title}
        if registration != "unmanaged":
            general["disallowUserRegistration"] = registration == "deny"
        settings.append({"name": "instance/settings/GENERAL", "generalSetting": general})

        # Memos manages this whole setting group; preserve app-managed fields
        # that the HA interface does not expose via the native ignoreChanges.
        ignored = [
            "generalSetting.disallowPasswordAuth",
            "generalSetting.disallowChangeUsername",
            "generalSetting.disallowChangeNickname",
            "generalSetting.weekStartDayOffset",
            "generalSetting.additionalStyle",
            "generalSetting.additionalScript",
            "generalSetting.customProfile.description",
            "generalSetting.customProfile.logoUrl",
        ]
        if not title:
            ignored.append("generalSetting.customProfile.title")
        if registration == "unmanaged":
            ignored.append("generalSetting.disallowUserRegistration")
        lifecycle.append({
            "resource": "instance/settings/GENERAL",
            "ignoreChanges": ignored,
        })

    if name:
        resource = "users/" + name
        desired.add(resource)
        users.append({
            "name": resource, "username": name, "role": "ADMIN",
            "password": "$" + "{file:" + str(PASSWORD_FILE) + "}",
        })
        lifecycle.append({"resource": resource, "preventDestroy": True, "writeOnlyVersion": version})

    removed = [{"resource": resource, "destroy": False} for resource in sorted(historical - desired)]
    output: dict = {}
    if settings:
        output["instanceSettings"] = settings
    if users:
        output["users"] = users
    if lifecycle:
        output["lifecycle"] = lifecycle
    if removed:
        output["removed"] = removed
    return output, historical | desired, password if name else None


def main() -> None:
    options = read_json(OPTIONS, {})
    historical = read_json(KNOWN, [])
    if not isinstance(options, dict) or not isinstance(historical, list) or not all(isinstance(s, str) for s in historical):
        raise ValueError("Invalid Home Assistant options or managed state JSON")
    configuration, known, password = render(options, set(historical))

    if password is not None:
        PASSWORD_FILE.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(PASSWORD_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as secret:
            secret.write(password)
        os.chmod(PASSWORD_FILE, 0o600)
    else:
        PASSWORD_FILE.unlink(missing_ok=True)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    atomic_json(CONFIG_DIR / "ha-generated.json", configuration)
    atomic_json(KNOWN, sorted(known))
    print("Memos HA configuration prepared: " + ", ".join(sorted(configuration)) if configuration else
          "Memos HA configuration: no HA-managed resources")


if __name__ == "__main__":
    main()
