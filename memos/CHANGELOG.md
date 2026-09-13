# Changelog

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
