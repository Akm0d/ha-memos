# Changelog

## 26.11.0-1

- Upgrade the packaged Memos container from 0.24.0 to 26.11.0 for a fresh Home Assistant installation.
- Add a six-hour stable-release check that verifies upstream Docker images before updating the Dockerfile, manifest, and changelog.
- Add updater regression tests, container build and HTTP startup smoke test CI.
- Rebrand the Home Assistant add-on repository to Akm0d/ha-memos and document the existing database migration requirements.

## 0.24.3

- Fix the container entrypoint so Memos actually stores its database and assets
  in Home Assistant's persistent `/data` directory
- Correct the documented data location and backup guidance

**Before updating:** Existing installations may still have their database in
the old container's `/var/opt/memos` volume. Stop the add-on and copy that
directory's contents to `/data` before rebuilding or updating.

## 0.24.0

- Initial release
- Based on Memos v0.24.0
- SQLite storage in /config/memos
- Ingress support for HA sidebar
