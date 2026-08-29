# Handoff para o desenvolvedor frontend

Este documento é o ponto de partida para o frontend. O contrato detalhado está em [`BACKEND_API.md`](BACKEND_API.md). A documentação executável fica em `http://localhost:8000/docs` no desenvolvimento e em `https://SEU_DOMINIO/docs` no servidor.

## O que já está pronto no backend

- API FastAPI versionada em `/api/v1`;
- PostgreSQL para câmeras e eventos;
- ingestão RTMP autorizada por chave cadastrada;
- HLS ao vivo com vídeo e áudio;
- estados `online`, `unstable` e `offline`;
- gravação contínua e playback por período;
- eventos com janela de pré e pós-alarme;
- rotação de chave RTMP;
- limite de 8 câmeras;
- retenção efetiva fixa em 7 dias;
- OpenAPI e validação consistente de erros.

## Endereços locais

| Serviço | URL |
|---|---|
| API | `http://localhost:8000/api/v1` |
| Swagger | `http://localhost:8000/docs` |
| OpenAPI | `http://localhost:8000/openapi.json` |
| Saúde | `http://localhost:8000/health` |
| HLS | devolvido no campo `hls_url` |
| Playback | devolvido no campo `url` ou `playback_url` |

Não fixe as portas de mídia no código do frontend. Consuma as URLs completas entregues pela API.

## Ambiente público

Defina `VITE_API_URL=https://SEU_DOMINIO/api/v1`. O servidor público exige autenticação HTTP e entrega API, HLS e playback pelo mesmo domínio HTTPS. Para o primeiro frontend, mantenha tudo no mesmo domínio; isso evita problemas de credenciais e CORS no player.

## Tipos TypeScript sugeridos

```ts
export type CameraStatus = "online" | "unstable" | "offline";

export interface Camera {
  id: number;
  name: string;
  location: string;
  audio_enabled: boolean;
  retention_days: 7;
  pre_alarm_seconds: number;
  post_alarm_seconds: number;
  stream_key: string;
  enabled: boolean;
  created_at: string;
  status: CameraStatus;
  rtmp_url: string;
  hls_url: string;
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
  playback_url: string;
}

export interface ApiError {
  detail: string | Array<{
    loc: Array<string | number>;
    msg: string;
    type: string;
  }>;
}
```

Os tipos também podem ser gerados automaticamente de `openapi.json` com `openapi-typescript`.

## Estrutura de frontend recomendada

```text
src/
├── api/
│   ├── client.ts          # base URL, JSON, ApiError e timeout
│   ├── cameras.ts         # CRUD, stream e gravações
│   └── events.ts          # alarmes e playback
├── components/
│   ├── CameraCard.tsx
│   ├── CameraStatus.tsx
│   ├── HlsPlayer.tsx
│   └── RecordingPlayer.tsx
├── pages/
│   ├── MosaicPage.tsx
│   ├── CamerasPage.tsx
│   └── HistoryPage.tsx
├── hooks/
│   ├── useCameras.ts
│   └── useHlsPlayer.ts
└── types/
    └── api.ts
```

O cliente HTTP deve ser a única camada que conhece a variável `VITE_API_URL`. Componentes não devem fazer `fetch` diretamente.

## Regras de tela

### Mosaico

- consulte `GET /cameras` a cada 10–15 segundos;
- renderize somente câmeras habilitadas;
- inicialize HLS apenas para `online` ou `unstable`;
- destrua a instância `hls.js` ao desmontar o card;
- comece o `<video>` com `muted` e permita ativação manual do áudio;
- não trate `unstable` como offline: mostre vídeo enquanto houver stream.

### Cadastro

- após `POST /cameras`, exiba `rtmp_url` com botão de copiar;
- `retention_days` deve ser enviado como `7` e pode aparecer bloqueado na interface;
- para desativar sem perder cadastro, use `PATCH {"enabled": false}`;
- exclusão e rotação de chave podem retornar `409` se o canal estiver conectado.

### Histórico

- converta seleções locais para UTC com `toISOString()`;
- consulte `GET /cameras/{id}/recordings?start=...&end=...`;
- use a URL retornada diretamente em `<video controls>`;
- não acrescente `format=mp4` novamente;
- eventos já devolvem a janela pronta em `playback_url`.

## Cliente HTTP mínimo

```ts
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Falha inesperada" }));
    throw Object.assign(new Error("API request failed"), {
      status: response.status,
      payload: error,
    });
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
```

## Checklist antes de integrar

1. Confirmar `GET /health` com `ok: true`.
2. Abrir `/docs` e conferir a versão `0.2.0`.
3. Criar uma câmera e copiar `rtmp_url`.
4. Publicar um stream H.264 + AAC.
5. Confirmar transição `unstable` → `online`.
6. Reproduzir `hls_url` com áudio.
7. Buscar gravações e abrir uma URL MP4.
8. Criar um evento e abrir `playback_url`.
9. Testar `404`, `409`, `422` e `503` no tratamento de erros.

## Limites conhecidos do MVP

- ambiente público protegido por um usuário/senha HTTP compartilhado, ainda sem contas individuais de operadores;
- retenção global fixa em 7 dias;
- status `unstable` representa os primeiros 20 segundos após a conexão;
- gravações preservadas em disco quando o cadastro/evento é removido;
- o servidor público já usa TLS; contas individuais, permissões, auditoria e observabilidade são evoluções necessárias para uso comercial.
