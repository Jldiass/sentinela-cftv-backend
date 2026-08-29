# Contrato do backend para o frontend

Base local: `http://localhost:8000`  
Base pública: `https://SEU_DOMINIO`  
API versionada: `/api/v1`  
OpenAPI interativo: `http://localhost:8000/docs`  
OpenAPI JSON: `http://localhost:8000/openapi.json`

O frontend não deve acessar PostgreSQL nem a API administrativa do MediaMTX. Ele conversa com FastAPI para metadados e usa apenas as URLs HLS/playback devolvidas pela API.

## Câmeras

### Listar

`GET /api/v1/cameras`

Por padrão retorna somente câmeras habilitadas. Para administração, use `?include_disabled=true`.

Campos importantes da resposta:

```json
{
  "id": 1,
  "name": "Entrada principal",
  "location": "Recepção",
  "stream_key": "cam-chave-gerada",
  "audio_enabled": true,
  "retention_days": 7,
  "pre_alarm_seconds": 30,
  "post_alarm_seconds": 60,
  "enabled": true,
  "status": "online",
  "rtmp_url": "rtmp://cftv.exemplo.com:1935/cam-chave-gerada",
  "hls_url": "https://cftv.exemplo.com/hls/cam-chave-gerada/index.m3u8",
  "effective_retention_hours": 168
}
```

Valores de `status`: `online`, `unstable` e `offline`. O frontend deve consultar a lista a cada 10–15 segundos. Não precisa consultar cada câmera individualmente.

### Criar

`POST /api/v1/cameras`

```json
{
  "name": "Entrada principal",
  "location": "Recepção",
  "audio_enabled": true,
  "retention_days": 7,
  "pre_alarm_seconds": 30,
  "post_alarm_seconds": 60
}
```

O backend gera a chave e devolve a URL RTMP completa. O limite atual é de 8 câmeras.

O campo `retention_days` representa a política-alvo de sete dias. `effective_retention_hours` informa a retenção global realmente aplicada pelo servidor. Na hospedagem beta gratuita ela pode ser menor por limitação de disco.

### Consultar, editar e remover

- `GET /api/v1/cameras/{id}`
- `PATCH /api/v1/cameras/{id}` — envie somente campos alterados.
- `DELETE /api/v1/cameras/{id}` — exige canal offline; remove cadastro e eventos, mas preserva arquivos gravados.
- `GET /api/v1/cameras/{id}/stream` — devolve chave e URLs.
- `POST /api/v1/cameras/{id}/stream-key/rotate` — exige canal offline.

Desabilitar com `PATCH {"enabled": false}` é preferível a excluir quando há histórico relevante.

## Vídeo ao vivo e áudio

Use `hls_url` em um player HLS. Em Chrome/Edge/Firefox, use `hls.js`; em Safari, atribua a URL diretamente ao `<video>`. Comece o player com `muted` por causa das regras de autoplay e ofereça um controle explícito para o operador ativar o áudio.

Nunca monte URLs no frontend. Use exatamente `hls_url`, `rtmp_url` e `playback_url` recebidas.

## Gravações

`GET /api/v1/cameras/{id}/recordings?start={RFC3339}&end={RFC3339}`

Resposta:

```json
[
  {
    "start": "2026-08-29T02:28:22Z",
    "duration": 120.5,
    "url": "https://cftv.exemplo.com/playback/get?...&format=mp4"
  }
]
```

`start` deve ser anterior a `end`. Datas devem ser enviadas em UTC/RFC3339. O link `url` pode ser usado em `<video controls>` ou para download.

## Eventos e pré-alarme

Criar disparo:

`POST /api/v1/cameras/{camera_id}/events`

```json
{
  "kind": "zona-03",
  "note": "Movimento na entrada",
  "happened_at": "2026-08-29T02:29:10Z"
}
```

`happened_at` é opcional; o servidor usa o horário atual. A resposta contém `clip_start`, `clip_duration` e `playback_url`, calculados com os tempos de pré e pós-alarme da câmera.

- `GET /api/v1/events?camera_id=1&limit=100`
- `GET /api/v1/events/{id}`
- `DELETE /api/v1/events/{id}` — remove o metadado, não o vídeo.

## Saúde e erros

`GET /health`

```json
{"ok":true,"database":"up","mediamtx":"up","active_streams":2,"version":"0.2.0","effective_retention_hours":168}
```

Erros seguem o formato FastAPI:

```json
{"detail":"Câmera não encontrada"}
```

Códigos importantes: `404` recurso inexistente, `409` conflito/limite/chave em uso, `422` validação e `503` mídia temporariamente indisponível.

## Ordem recomendada de implementação do frontend

1. Cliente HTTP tipado e tratamento central de erros.
2. Lista/cadastro/edição de câmeras.
3. Mosaico HLS com áudio controlado pelo operador.
4. Indicadores de estado com polling a cada 10–15 segundos.
5. Busca de gravações por período.
6. Timeline e lista de eventos com playback.
7. Login individual, permissões e auditoria na evolução para uso comercial.
