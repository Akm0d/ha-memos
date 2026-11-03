#!/bin/sh
set -eu
umask 077

# /data is persistent HA app storage. Never delete or replace it on upgrade.
mkdir -p /data /etc/memos/config

# Generate only explicitly requested declarative resources. HA options live
# in /data/options.json; the bootstrap password stays out of generated JSON.
python3 /usr/local/lib/configure-memos.py
/usr/local/memos/memos config validate --config-dir /etc/memos/config

# Go PID 1 supervises the official Memos process plus ingress/API listeners.
exec /usr/local/bin/ha-memos-gateway
