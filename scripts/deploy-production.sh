#!/usr/bin/env bash
set -Eeuo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_dir}"

if [[ ! -f .env.production ]]; then
  echo "Arquivo .env.production ausente. Copie .env.production.example e configure-o." >&2
  exit 1
fi

docker compose --env-file .env.production -f compose.prod.yml config --quiet
docker compose --env-file .env.production -f compose.prod.yml up -d --build --remove-orphans
docker compose --env-file .env.production -f compose.prod.yml ps

for attempt in {1..12}; do
  if docker compose --env-file .env.production -f compose.prod.yml exec -T backend \
    python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"; then
    echo "Backend saudável."
    exit 0
  fi
  sleep 5
done

echo "Backend não ficou saudável no tempo esperado." >&2
docker compose --env-file .env.production -f compose.prod.yml logs --tail=100 backend mediamtx caddy
exit 1
