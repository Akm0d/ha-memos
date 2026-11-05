#!/usr/bin/env bash
set -euo pipefail
name="memos-addon-ci-$RANDOM"
data="$(mktemp -d)"
html="$(mktemp)"
trap 'docker logs --tail 90 "$name" 2>/dev/null || true; docker rm -f "$name" >/dev/null 2>&1 || true; rm -f "$html"; rm -rf "$data"' EXIT

docker run -d --name "$name" \
  -e MEMOS_CI_ALLOW_LOOPBACK=1 \
  --network host \
  -v "$data:/data" \
  memos-addon-ci

ready=false
for attempt in $(seq 1 90); do
  if curl -fsS --max-time 3 http://127.0.0.1:5230/healthz | grep -q 'Service ready'; then
    ready=true
    break
  fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$name")" != "true" ]]; then
    echo "Memos container stopped unexpectedly" >&2
    exit 1
  fi
  sleep 2
done
[[ "$ready" == "true" ]] || { echo "Memos health check timed out" >&2; exit 1; }

# Standalone host listener serves the frontend and OAuth callback.
curl -fsS --max-time 8 http://127.0.0.1:5230/ -o "$html"
grep -Fq 'window.__MEMOS_INGRESS_BASE__=""' "$html"
grep -Fq '<base href="/">' "$html"
[[ "$(curl -sS -o /dev/null -w '%{http_code}' 'http://127.0.0.1:5230/auth/callback?code=test&state=test')" == "200" ]]

asset="$(grep -oE 'src="./assets/[^"]+\.js"' "$html" | head -n1 | cut -d '"' -f2 | sed 's|^./||')"
[[ -n "$asset" ]] || { echo "Missing standalone frontend JS asset" >&2; exit 1; }
curl -fsS --max-time 8 "http://127.0.0.1:5230/$asset" -o /dev/null

# MCP remains available on the standalone listener; unrelated paths use the UI router.
[[ "$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:5230/mcpevil)" == "404" ]]
mcp_result="$(mktemp)"
mcp_init='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"memos-addon-ci","version":"1.0.0"}}}'
curl -fsS --max-time 10 \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data "$mcp_init" http://127.0.0.1:5230/mcp -o "$mcp_result"
python3 - "$mcp_result" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    response = json.load(f)
assert response.get("jsonrpc") == "2.0", response
assert response.get("id") == 1, response
assert response.get("result", {}).get("serverInfo"), response
PY
rm -f "$mcp_result"

# The ingress listener rejects clients without a verified Supervisor source.
# CI explicitly grants loopback as an exception, but never a bare ingress path.
[[ "$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/)" == "400" ]]

prefix="/api/hassio_ingress/ci_session"
curl -fsS --max-time 8 -H "X-Ingress-Path: $prefix/" http://127.0.0.1:8099/ -o "$html"
grep -Fq "window.__MEMOS_INGRESS_BASE__" "$html"
grep -Fq "<base href=\"$prefix/\">" "$html"

# The browser receives relative hashed assets from the same ingress session.
asset="$(grep -oE 'src="\./assets/[^"]+\.js"' "$html" | head -n1 | cut -d '"' -f2 | sed 's|^\./||')"
[[ -n "$asset" ]] || { echo "Missing frontend JS asset" >&2; exit 1; }
curl -fsS --max-time 8 -H "X-Ingress-Path: $prefix/" "http://127.0.0.1:8099/$asset" -o /dev/null
curl -fsS --max-time 8 -H "X-Ingress-Path: $prefix/" http://127.0.0.1:8099/healthz | grep -q 'Service ready'

echo "Memos standalone web/API/MCP and Home Assistant ingress smoke tests passed"
