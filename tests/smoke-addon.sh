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

# Host port is not the browser UI and cannot reveal its frontend bundles.
[[ "$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:5230/)" == "404" ]]
[[ "$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:5230/assets/index.js)" == "404" ]]
[[ "$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:5230/auth)" == "404" ]]

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

echo "Memos API-only and Home Assistant ingress smoke tests passed"
