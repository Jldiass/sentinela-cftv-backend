#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root: sudo $0" >&2
  exit 1
fi

if [[ ! -r /etc/os-release ]]; then
  echo "Distribuição não identificada. Este script suporta Ubuntu." >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID}" != "ubuntu" ]]; then
  echo "Sistema não suportado: ${ID}. Use Ubuntu 22.04 ou 24.04." >&2
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl git ufw

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

dpkg_arch="$(dpkg --print-architecture)"
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${VERSION_CODENAME}
Components: stable
Architectures: ${dpkg_arch}
Signed-By: /etc/apt/keyrings/docker.asc
EOF

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

install -d -m 0755 /srv/sentinela
install -d -m 0755 /srv/sentinela/recordings
install -d -m 0700 /srv/sentinela/postgres

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 1935/tcp
ufw --force enable

echo "Servidor preparado. Clone o repositório e configure .env.production."
