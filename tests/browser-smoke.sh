#!/usr/bin/env bash
set -euo pipefail

npm install --no-save --no-audit --no-fund playwright@1.57.0
npx playwright install --with-deps chromium

name="memos-browser-ci-$RANDOM"
data="$(mktemp -d)"
proxy_pid=""
trap '
  if [[ -n "$proxy_pid" ]]; then kill "$proxy_pid" 2>/dev/null || true; fi
  docker logs --tail 75 "$name" 2>/dev/null || true
  docker rm -f "$name" >/dev/null 2>&1 || true
  rm -rf "$data"
' EXIT

docker run -d --name "$name" --network host \
  -e MEMOS_CI_ALLOW_LOOPBACK=1 \
  -v "$data:/data" memos-addon-ci

ready=false
for attempt in $(seq 1 90); do
  if curl -fsS --max-time 3 http://127.0.0.1:5230/healthz 2>/dev/null | grep -q 'Service ready'; then
    ready=true
    break
  fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$name")" != "true" ]]; then
    echo "Memos browser fixture container stopped" >&2
    exit 1
  fi
  sleep 2
done
[[ "$ready" == "true" ]] || { echo "Memos backend was not ready" >&2; exit 1; }

python3 tests/mock_supervisor_ingress.py &
proxy_pid=$!
sleep 1
node tests/browser-ingress.mjs
