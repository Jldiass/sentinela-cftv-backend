FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_URL=/api/v1
RUN npm run build

FROM python:3.12-slim

ARG MEDIAMTX_VERSION=1.20.1
ARG TARGETARCH=amd64

RUN apt-get update \
    && apt-get install -y --no-install-recommends apache2-utils ca-certificates curl nginx \
    && curl -fsSL \
       "https://github.com/bluenviron/mediamtx/releases/download/v${MEDIAMTX_VERSION}/mediamtx_v${MEDIAMTX_VERSION}_linux_${TARGETARCH}.tar.gz" \
       | tar -xz -C /usr/local/bin mediamtx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/alembic.ini ./alembic.ini
COPY backend/migrations ./migrations
COPY mediamtx/railway.yml /etc/mediamtx.yml
COPY railway/nginx.conf /etc/nginx/nginx.conf
COPY railway/start.sh /start.sh
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html

RUN chmod +x /start.sh && mkdir -p /data/recordings

ENV PORT=8080 \
    MEDIAMTX_API_URL=http://127.0.0.1:9997 \
    MEDIAMTX_PLAYBACK_URL=http://127.0.0.1:9996 \
    PUBLIC_HLS_BASE_URL=/hls \
    PUBLIC_PLAYBACK_BASE_URL=/playback \
    RECORD_DELETE_AFTER=1h

EXPOSE 8080 1935

CMD ["/start.sh"]
