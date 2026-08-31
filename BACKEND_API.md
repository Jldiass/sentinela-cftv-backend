# Contrato da API — Malupe Cam Beta

Versão: `0.3.4`
Base local: `http://localhost:8000`
Prefixo: `/api/v1`
OpenAPI: `/openapi.json`
Swagger: `/docs`

JSON usa nomes em `snake_case`. Datas são RFC3339/ISO 8601 e devem incluir fuso horário, preferencialmente UTC com sufixo `Z`.

## Saúde

### `GET /health`

```json
{
  "ok": true,
  "database": "up",
  "mediamtx": "up",
  "active_streams": 2,
  "version": "0.3.4",
  "effective_retention_hours": 1
}
```

`ok` somente é `true` quando banco e MediaMTX respondem. `effective_retention_hours` é a fonte oficial da retenção mostrada no frontend.

## Câmeras

### Listar

`GET /api/v1/cameras`

Retorna apenas câmeras habilitadas. Use `?include_disabled=true` na administração.

```json
[
  {
    "id": 1,
    "name": "Entrada principal",
    "location": "Recepção",
    "audio_enabled": true,
    "pre_alarm_seconds": 30,
    "post_alarm_seconds": 60,
    "stream_key": "cam-chave-aleatoria",
    "enabled": true,
    "created_at": "2026-08-29T12:00:00Z",
    "status": "online",
    "stream_path": "live/cam-chave-aleatoria",
    "rtmp_server_url": "rtmp://host:1935/live",
    "rtmp_url": "rtmp://host:1935/live/cam-chave-aleatoria",
    "hls_url": "https://host/hls/live/cam-chave-aleatoria/index.m3u8?cookieCheck=1",
    "effective_retention_hours": 1
  }
]
```

`status` pode ser `online`, `unstable` ou `offline`.

### Criar

`POST /api/v1/cameras`

```json
{
  "name": "Entrada principal",
  "location": "Recepção",
  "audio_enabled": true,
  "pre_alarm_seconds": 30,
  "post_alarm_seconds": 60
}
```

Resposta: `201` com a câmera completa. O backend gera `rtmp_server_url`, `stream_key`, `rtmp_url` e `hls_url`. Há no máximo oito cadastros.

Campos desconhecidos retornam `422`. Não envie retenção no cadastro: ela é global em uma hora.

### Consultar

`GET /api/v1/cameras/{camera_id}`

Resposta: `200` com a câmera ou `404`.

### Editar

`PATCH /api/v1/cameras/{camera_id}`

Envie somente campos alterados:

```json
{
  "name": "Portão social",
  "enabled": false
}
```

Campos aceitos: `name`, `location`, `audio_enabled`, `pre_alarm_seconds`, `post_alarm_seconds` e `enabled`.

### Excluir

`DELETE /api/v1/cameras/{camera_id}`

Resposta `204`. Se houver publicação ativa, retorna `409`; desconecte a câmera antes. A exclusão remove cadastro e eventos relacionados. Arquivos ainda existentes seguem a limpeza automática de uma hora.

### Credenciais de stream

`GET /api/v1/cameras/{camera_id}/stream`

```json
{
  "camera_id": 1,
  "stream_key": "cam-chave-aleatoria",
  "stream_path": "live/cam-chave-aleatoria",
  "rtmp_server_url": "rtmp://host:1935/live",
  "rtmp_url": "rtmp://host:1935/live/cam-chave-aleatoria",
  "hls_url": "https://host/hls/live/cam-chave-aleatoria/index.m3u8?cookieCheck=1"
}
```

Há dois formatos de configuração possíveis:

- Mibo Smart/Mibo Cam: apague o conteúdo anterior do campo `URL RTMP` e cole
  somente `rtmp_url`, uma única vez;
- equipamento com campos separados: servidor = `rtmp_server_url` e chave =
  `stream_key`.

Nunca repita a URL ou a chave. A API garante que a URL completa é
`rtmp_server_url + "/" + stream_key` e inclui a chave exatamente uma vez.
O segmento `live` é a aplicação RTMP; `stream_path` é o caminho interno usado
por status, HLS, gravação e playback.

### Trocar chave RTMP

`POST /api/v1/cameras/{camera_id}/stream-key/rotate`

Exige canal offline. Retorna `409` se conectado e `503` se não for possível confirmar o estado do MediaMTX. Depois da troca, a câmera deve ser reconfigurada com a nova URL.

## Ao vivo e áudio

O frontend usa `hls_url`. Em Chrome, Edge e Firefox use `hls.js`; Safari pode usar HLS nativo. O elemento `<video>` deve iniciar com `muted` para cumprir as regras de autoplay, oferecendo ativação manual do áudio.

Não monte a URL a partir de `stream_key`. Sempre use `hls_url` devolvida.

## Gravações

### Buscar por período

```http
GET /api/v1/cameras/{camera_id}/recordings?start=2026-08-29T15:30:00Z&end=2026-08-29T16:00:00Z
```

Parâmetros são opcionais. Quando ambos existem, `start` deve ser anterior a `end`.

```json
[
  {
    "start": "2026-08-29T15:30:00Z",
    "duration": 600.5,
    "url": "https://host/playback/get?path=cam-chave-aleatoria&start=...&duration=600.5&format=mp4"
  }
]
```

Use `url` diretamente no player ou download. Conteúdo anterior à última hora já foi removido e não é recuperável. A limpeza física ocorre por segmentos de 10 segundos, portanto pode existir uma pequena tolerância operacional em torno do limite.

## Eventos e pré-alarme

### Criar

`POST /api/v1/cameras/{camera_id}/events`

```json
{
  "kind": "zona-03",
  "note": "Movimento na entrada",
  "happened_at": "2026-08-29T15:45:10Z"
}
```

`happened_at` é opcional; sem ele, o backend usa o horário atual. O backend rejeita datas futuras e eventos cujo início do pré-alarme já esteja fora da retenção.

Resposta imediatamente após o disparo:

```json
{
  "id": 10,
  "camera_id": 1,
  "kind": "zona-03",
  "note": "Movimento na entrada",
  "happened_at": "2026-08-29T15:45:10Z",
  "clip_start": "2026-08-29T15:44:40Z",
  "clip_duration": 90,
  "playback_url": null,
  "clip_status": "pending",
  "available_until": "2026-08-29T16:44:40Z"
}
```

Estados:

- `pending`: o pós-alarme ainda está sendo gravado; `playback_url` é `null`;
- `available`: clipe finalizado e dentro da última hora; há URL;
- `expired`: início do clipe ultrapassou a retenção; não há URL.

Os metadados expirados são removidos em segundo plano a cada minuto.

### Listar

`GET /api/v1/events?camera_id=1&limit=100`

`camera_id` é opcional. `limit` aceita 1–500.

### Consultar e excluir

- `GET /api/v1/events/{event_id}`
- `DELETE /api/v1/events/{event_id}`

Excluir remove o metadado, não força a exclusão antecipada do arquivo gravado.

## Autorização do MediaMTX

`POST /internal/mediamtx/auth` é interno e não faz parte do contrato do frontend. Em produção, o Caddy bloqueia `/internal/*`. Publicações RTMP somente são aceitas quando o caminho corresponde à chave de uma câmera habilitada.

## Erros

Erro de regra:

```json
{"detail":"Câmera não encontrada"}
```

Erro de validação:

```json
{
  "detail": [
    {
      "type": "extra_forbidden",
      "loc": ["body", "retention_days"],
      "msg": "Extra inputs are not permitted",
      "input": 7
    }
  ]
}
```

| Código | Significado |
|---:|---|
| 201 | recurso criado |
| 204 | exclusão concluída |
| 404 | recurso não encontrado |
| 409 | conflito de estado ou limite |
| 422 | JSON, campo ou data inválida |
| 503 | serviço de mídia indisponível |

## CORS e ambiente público

Em desenvolvimento, as origens padrão são `localhost:3000`, `localhost:5173` e `localhost:8000`. Em produção, configure `CORS_ORIGINS` com os endereços HTTPS do frontend, separados por vírgula.

API, HLS e playback devem preferencialmente estar no mesmo domínio. O frontend nunca deve acessar as portas administrativas `9996` ou `9997` diretamente.
