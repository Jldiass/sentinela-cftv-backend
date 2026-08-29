# Handoff do frontend — Malupe Cam Beta

Este arquivo é o ponto de partida do desenvolvedor frontend. O backend já define cadastro, mídia, status, histórico e alarmes. O frontend deve consumir o contrato, sem montar URLs de vídeo manualmente.

## Endereços

Desenvolvimento:

```text
API:      http://localhost:8000/api/v1
Swagger:  http://localhost:8000/docs
OpenAPI:  http://localhost:8000/openapi.json
Saúde:    http://localhost:8000/health
```

Servidor público:

```text
API:      https://SEU_DOMINIO/api/v1
Swagger:  https://SEU_DOMINIO/docs
Saúde:    https://SEU_DOMINIO/health
```

Configure no frontend:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

Em produção, substitua pelo domínio HTTPS. Componentes não devem conhecer `localhost`; apenas o cliente HTTP deve ler `VITE_API_URL`.

## Regra obrigatória de retenção

O beta mantém uma janela móvel global de **1 hora**. O cadastro de câmera não possui campo configurável de retenção.

Exemplo às 17:00:

```text
Disponível: 16:00 até 17:00
Expirado:   tudo que começou antes de 16:00
```

A API devolve `effective_retention_hours: 1`. Use esse campo na interface; não escreva “7 dias” no código ou no layout.

## Tipos TypeScript

```ts
export type CameraStatus = "online" | "unstable" | "offline";
export type ClipStatus = "pending" | "available" | "expired";

export interface Camera {
  id: number;
  name: string;
  location: string;
  audio_enabled: boolean;
  pre_alarm_seconds: number;
  post_alarm_seconds: number;
  stream_key: string;
  enabled: boolean;
  created_at: string;
  status: CameraStatus;
  rtmp_url: string;
  hls_url: string;
  effective_retention_hours: number;
}

export interface CameraCreate {
  name: string;
  location?: string;
  audio_enabled?: boolean;
  pre_alarm_seconds?: number;
  post_alarm_seconds?: number;
}

export interface Recording {
  start: string;
  duration: number;
  url: string;
}

export interface AlarmEvent {
  id: number;
  camera_id: number;
  kind: string;
  note: string;
  happened_at: string;
  clip_start: string;
  clip_duration: number;
  playback_url: string | null;
  clip_status: ClipStatus;
  available_until: string;
}

export interface Health {
  ok: boolean;
  database: "up" | "down";
  mediamtx: "up" | "down";
  active_streams: number;
  version: string;
  effective_retention_hours: number;
}

export interface ApiError {
  detail: string | Array<{
    loc: Array<string | number>;
    msg: string;
    type: string;
  }>;
}
```

Os tipos podem ser gerados com `openapi-typescript` a partir de `/openapi.json`.

## Cliente HTTP mínimo

```ts
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({
      detail: "Falha inesperada",
    }));
    throw Object.assign(new Error("API request failed"), {
      status: response.status,
      payload,
    });
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
```

## Estrutura sugerida

```text
src/
├── api/
│   ├── client.ts
│   ├── cameras.ts
│   └── events.ts
├── components/
│   ├── CameraCard.tsx
│   ├── CameraStatus.tsx
│   ├── HlsPlayer.tsx
│   ├── RecordingPlayer.tsx
│   └── RetentionBadge.tsx
├── hooks/
│   ├── useCameras.ts
│   └── useHlsPlayer.ts
├── pages/
│   ├── MosaicPage.tsx
│   ├── CamerasPage.tsx
│   └── HistoryPage.tsx
└── types/api.ts
```

## Ordem recomendada de implementação

1. Cliente HTTP e tratamento central de erros.
2. Página de cadastro/lista/edição de câmeras.
3. Player HLS e mosaico 1, 4 ou 8 câmeras.
4. Indicadores de estado com polling.
5. Busca de gravações limitada à última hora.
6. Lista de eventos e estados dos clips.
7. Acabamento visual e responsividade.

## Cadastro de câmera

Crie com `POST /cameras`. Exemplo:

```json
{
  "name": "Entrada principal",
  "location": "Recepção",
  "audio_enabled": true,
  "pre_alarm_seconds": 30,
  "post_alarm_seconds": 60
}
```

Após criar, exiba `rtmp_url` com botão de copiar. Não aceite `stream_key` digitada pelo operador; ela é gerada pelo backend.

Não envie `retention_days` ou `retention_hours` no cadastro. A política é global e devolvida em `effective_retention_hours`.

## Mosaico e player HLS

- consulte `GET /cameras` a cada 10–15 segundos;
- renderize somente câmeras habilitadas;
- abra HLS para `online` e `unstable`;
- mostre placeholder para `offline`;
- comece o `<video>` com `muted` por causa do autoplay;
- permita que o operador ative áudio manualmente;
- destrua a instância `hls.js` ao desmontar o card;
- não recrie o player a cada polling se a URL não mudou.

Safari pode usar HLS nativo. Chrome, Edge e Firefox devem usar `hls.js`.

## Status das câmeras

| Valor | Comportamento de tela |
|---|---|
| `online` | verde e player ativo |
| `unstable` | amarelo e player ativo; canal acabou de conectar |
| `offline` | vermelho e player parado |

Se `/health` indicar `mediamtx: down`, mostre indisponibilidade do serviço, não converta tudo silenciosamente em falha individual de câmera.

## Histórico de gravações

Use:

```http
GET /cameras/{id}/recordings?start={RFC3339}&end={RFC3339}
```

Regras:

- limite o seletor de período à última hora;
- converta horário local para UTC com `toISOString()`;
- `start` deve ser anterior a `end`;
- use a propriedade `url` recebida diretamente em `<video controls>`;
- lista vazia significa que não há segmento naquele intervalo;
- não tente recuperar vídeo anterior à janela móvel.

## Eventos e pré-alarme

Ao criar um evento, o backend calcula a janela com os segundos anteriores e posteriores configurados na câmera.

O frontend deve tratar:

| `clip_status` | `playback_url` | Tela |
|---|---|---|
| `pending` | `null` | “Finalizando clipe” e atualizar depois |
| `available` | URL | botão “Reproduzir” |
| `expired` | `null` | “Vídeo expirado” |

Um evento novo fica `pending` até terminar o pós-alarme. Não renderize um link quando `playback_url` for `null`.

## Erros que precisam de tratamento

| HTTP | Situação comum |
|---:|---|
| 404 | câmera/evento inexistente |
| 409 | limite de 8, câmera conectada durante exclusão/rotação ou câmera desabilitada |
| 422 | formulário inválido, campo desconhecido ou data fora da retenção |
| 503 | MediaMTX/playback indisponível |

Formato comum:

```json
{"detail":"Câmera não encontrada"}
```

## Checklist de entrega do frontend

- [ ] `GET /health` mostra API e mídia disponíveis.
- [ ] Nenhum componente contém URL fixa de HLS ou playback.
- [ ] Cadastro exibe e copia a URL RTMP.
- [ ] Mosaico reproduz H.264 + AAC.
- [ ] Áudio só é habilitado após ação do usuário.
- [ ] Status atualiza sem desmontar players desnecessariamente.
- [ ] Busca respeita a última hora.
- [ ] Evento pendente não mostra link quebrado.
- [ ] Evento disponível abre o MP4.
- [ ] Erros 404, 409, 422 e 503 têm mensagens amigáveis.
- [ ] A interface mostra “Histórico: 1 hora”.

## Fora do escopo deste beta

- contas individuais e permissões por operador;
- PTZ;
- reconhecimento/analytics;
- notificações push;
- retenção individual por câmera;
- recuperação de arquivos já expirados.
