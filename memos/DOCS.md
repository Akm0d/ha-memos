# Memos for Home Assistant

Open-source, self-hosted note-taking tool built for quick capture.

## Features

- **Instant Capture** — Timeline-first UI. Open, write, done.
- **Markdown Native** — Full Markdown support with preview.
- **Self-hosted** — Your data stays on your Home Assistant.
- **Lightweight** — Minimal resource usage with SQLite storage.
- **Mobile Friendly** — Responsive UI works great on phones.

## Installation

1. Add this addon repository to Home Assistant
2. Install the Memos addon
3. Start the addon
4. Access via the sidebar or `http://your-ha:5230`

## First Run

On first access, you'll be prompted to create an admin account.

## Data Storage

All data is stored in the add-on's persistent `/data` directory, including:

- SQLite database
- Uploaded assets

Home Assistant Supervisor retains this directory when the add-on restarts or
updates. Uninstalling the add-on and choosing to remove its data will delete it.

### Upgrading from 0.24.2 or earlier

Those add-on versions could run Memos with its database in the container's
`/var/opt/memos` volume instead of `/data`. Before updating, copy the complete
contents of `/var/opt/memos` from the existing container into its `/data`
directory. Stop Memos while copying so the SQLite database and its WAL files are
consistent. Updating or rebuilding first may make the old container volume
inaccessible.

## Backup

Include the Memos add-on in your Home Assistant backup configuration. Keep at
least one backup on another device or remote backup location.

## Links

- [Memos Documentation](https://usememos.com/docs)
- [Memos GitHub](https://github.com/usememos/memos)
- [Live Demo](https://demo.usememos.com/)

## Maintained Add-on and Release Updates

The maintained add-on repository is https://github.com/Akm0d/ha-memos.
The upstream Memos project is https://github.com/usememos/memos.

A GitHub Actions workflow checks upstream stable releases every six hours,
verifies that the corresponding versioned Docker image exists, and updates
the add-on manifest, Dockerfile, and changelog. The version syntax mirrors
upstream Memos, plus a packaging revision suffix (such as 26.11.0-1).

New releases appear in Home Assistant after its add-on repository refreshes.
Automatic installation requires Home Assistant automatic updates to be enabled.

### Migrating existing Memos installations

If moving an existing Docker-hosted Memos database and attachments:

1. Identify the version running on the old host and back up the entire data
   directory, including SQLite WAL/SHM files when present.
2. Stop the writer and take a consistent backup. Work on a separate copy.
3. Follow the documented upstream upgrade path. Versions 0.22–0.30 need
   a successful run of v0.31.0 before 26.11.0. Versions older than 0.22
   need v0.25.3 and then v0.31.0 first.
4. Install the Home Assistant add-on, stop it before populating the
   add-on's persistent /data directory, and copy the verified migrated data.
5. Start the add-on, inspect logs, and verify memos, users, and attachments.
6. Keep the original host backup and Salt configuration available for
   recovery until the cutover is confirmed.

A Home Assistant add-on backup protects the destination, but does not
substitute for a backup taken before Memos changes its database schema.
See https://usememos.com/docs/operations/upgrade.

## Licensing

The inherited Home Assistant wrapper originated in
https://github.com/nikopolv/ha-addons, which currently has no published
license. New Akm0d-authored release automation is separately covered by
LICENSE-AKM0D.md. This does not relicense third-party files.
