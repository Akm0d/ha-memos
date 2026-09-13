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
