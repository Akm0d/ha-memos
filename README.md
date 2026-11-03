# Memos Home Assistant Add-on — Akm0d

Home Assistant add-on for [Memos](https://github.com/usememos/memos), a
self-hosted note-taking application.

## Install

1. In Home Assistant, open **Settings → Add-ons → Add-on Store**.
2. Open **⋮ → Repositories**.
3. Add **https://github.com/Akm0d/ha-memos**.
4. Refresh the store, select **Memos**, then install.

[Add this repository to Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FAkm0d%2Fha-memos)

Memos is served through Home Assistant ingress and optionally through port 5230.
Its SQLite database and local assets persist in the add-on data directory.

## Stable release automation

GitHub Actions checks [official Memos stable releases](https://github.com/usememos/memos/releases)
every six hours. When upstream publishes a new stable release and its pinned
Docker image exists, the workflow updates the image tag, Home Assistant add-on
version, and changelog, then commits the change. Release candidates are ignored.
New versions use upstream MAJOR.MINOR.PATCH with a packaging suffix, such as
26.11.0-1; add-on-only revisions can use -2, -3, etc.

The PR test workflow tests the release updater, builds the add-on image, and
smoke-tests HTTP startup. Home Assistant must refresh the repository and have
automatic add-on updates enabled to install new versions automatically.

## Moving existing data from Fenix

**Do not copy an old SQLite database directly into a new-version add-on.**
Memos migrates its database at startup, and rollback requires a backup.

- From Memos 0.22 through 0.30: run 0.31.0 successfully against a **copy**
  of the database and attachments, then use 26.11.0.
- From before Memos 0.22: run 0.25.3, then 0.31.0, then 26.11.0.
- Fresh installations may start directly on the latest stable version.

Back up your Fenix database and attachments, verify the intermediate migration
on a separate copy, and only then move the migrated files into the HA add-on
persistent data directory. Stop processes before copying SQLite files. Do not
remove the original Salt-managed service until the HA instance is verified.

See [Memos upgrade guidance](https://usememos.com/docs/operations/upgrade)
and [add-on documentation](memos/DOCS.md).

## Attribution and licensing

This fork builds on [nikopolv/ha-addons](https://github.com/nikopolv/ha-addons).
The original add-on wrapper has no published license; the scoped
[MIT license for new Akm0d automation](LICENSE-AKM0D.md) does not alter the
original author's rights. The separate upstream Memos application is MIT-licensed.
