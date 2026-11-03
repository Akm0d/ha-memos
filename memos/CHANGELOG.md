# Changelog

## 26.11.0-4

- Forward native Memos `/mcp` (Streamable HTTP) through the agent-facing
  API-only listener on TCP 5230, without exposing browser UI routes.
- Add route-isolation regression tests and a live MCP initialize smoke test.
- Document token-based MCP agent access and retain Home Assistant ingress
  as the separate browser interface.

## 26.11.0-3

- Restore Home Assistant ingress through an internal supervisor-only adapter.
- Build a version-matched Memos frontend with relative assets and an ingress-aware
  router, Connect RPC client, SSE endpoint, and attachment URLs.
- Expose an API-only listener on port 5230 for agents; preserve Memos authentication.
- Add opt-in Home Assistant Configuration options to generate native Memos
  declarative admin bootstrap, password rotation, access policy and general settings.
- Keep the upstream Memos 26.11.0 runtime binary unchanged and add release
  compatibility checks for the independently compiled frontend.

## 26.11.0-2

- Use Home Assistant's direct Web UI launcher instead of ingress for Memos, which generates root-relative frontend asset URLs incompatible with Home Assistant ingress paths.
- Keep host port 5230 available for browser users and API clients; Memos handles user authentication directly.
- Preserve the upstream 26.11.0 Docker image and six-hour stable release tracking.

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
