#!/usr/bin/env bash
set -euo pipefail

: "${BASIC_AUTH_USER:?Defina BASIC_AUTH_USER no Railway}"
: "${BASIC_AUTH_PASSWORD:?Defina BASIC_AUTH_PASSWORD no Railway}"
: "${AUTH_JWT_SECRET:?Defina AUTH_JWT_SECRET no Railway}"

export DATABASE_URL="${DATABASE_URL:-sqlite+pysqlite:////data/malupe-cam.db}"
export PUBLIC_RTMP_BASE_URL="${PUBLIC_RTMP_BASE_URL:-rtmp://localhost:1935}"
export PUBLIC_HLS_BASE_URL="${PUBLIC_HLS_BASE_URL:-/hls}"
export PUBLIC_PLAYBACK_BASE_URL="${PUBLIC_PLAYBACK_BASE_URL:-/playback}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:8080}"

mkdir -p /data/recordings
htpasswd -bcB /etc/nginx/.htpasswd "$BASIC_AUTH_USER" "$BASIC_AUTH_PASSWORD" >/dev/null
alembic -c /app/alembic.ini upgrade head

uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-config app/logging.json &
api_pid=$!
mediamtx /etc/mediamtx.yml &
media_pid=$!
nginx -g "daemon off;" &
web_pid=$!

shutdown() {
  kill "$api_pid" "$media_pid" "$web_pid" 2>/dev/null || true
  wait "$api_pid" "$media_pid" "$web_pid" 2>/dev/null || true
}

trap shutdown EXIT INT TERM
wait -n "$api_pid" "$media_pid" "$web_pid"
exit_code=$?
exit "$exit_code"
