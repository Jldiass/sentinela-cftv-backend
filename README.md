# Malupe Cam — Backend CFTV Beta

Backend próprio para monitoramento de até **8 câmeras RTMP**, com áudio, HLS ao vivo, gravação contínua, histórico móvel de **1 hora**, status de conexão e eventos com pré/pós-alarme.

Versão atual da API: **0.3.2**.

## Regra do histórico de 1 hora

A retenção é global e automática. O MediaMTX grava arquivos fMP4 em segmentos de 10 segundos e remove cada segmento quando ele completa uma hora.

Exemplo às 17:00:

```text
16:00 ------------------------------ 17:00
       conteúdo disponível

15:59:50 -> apagado automaticamente
16:00:00 -> ainda disponível
```

É uma janela móvel: não existe uma limpeza única no fim do dia. A remoção acontece gradualmente, acompanhando os segmentos. A API informa `effective_retention_hours: 1` para o frontend exibir a política real.

## O que está pronto

- cadastro, edição, desativação e exclusão de câmeras;
- limite global de 8 câmeras;
- chave e URL RTMP individual geradas pelo backend;
- autorização de publicação: somente chaves cadastradas e habilitadas publicam;
- vídeo H.264 e áudio AAC ao vivo por HLS;
- mosaico demonstrativo;
- estados `online`, `unstable` e `offline`;
- gravação contínua 24 horas com retenção móvel de 1 hora;
- busca de gravações por data/hora;
- eventos com pré e pós-alarme;
- clips com estado `pending`, `available` ou `expired`;
- remoção automática dos metadados de eventos expirados;
- PostgreSQL, logs, healthcheck e Docker Compose;
- proxy HTTPS e proteção por usuário/senha para publicação em servidor;
- testes unitários, testes de contrato e pipeline do GitHub Actions.

## Arquitetura

```text
Câmera / encoder (H.264 + AAC)
             |
             | RTMP + chave individual
             v
          MediaMTX --------> HLS ao vivo --------> Frontend
             |
             +-------------> segmentos fMP4
                                     |
                                     +--> exclusão após 1 hora

Frontend --------> FastAPI --------> PostgreSQL
                      |
                      +--> cadastro, status, histórico e eventos
```

O frontend nunca acessa PostgreSQL nem a API administrativa do MediaMTX. Ele usa apenas o FastAPI e as URLs completas devolvidas pela API.

## Arquivos importantes para o frontend

1. [`FRONTEND_HANDOFF.md`](FRONTEND_HANDOFF.md) — instruções de implementação, tipos TypeScript e checklist.
2. [`BACKEND_API.md`](BACKEND_API.md) — contrato de todos os endpoints e exemplos.
3. `http://localhost:8000/docs` — Swagger executável quando o ambiente está ativo.
4. `http://localhost:8000/openapi.json` — contrato OpenAPI para gerar tipos automaticamente.

## Executar para desenvolvimento

Pré-requisitos: Docker Desktop ou Docker Engine com Compose.

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

No Windows PowerShell, copie o arquivo com:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Endereços locais:

| Serviço | Endereço |
|---|---|
| demonstração e API | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |
| saúde | `http://localhost:8000/health` |
| ingestão RTMP | `rtmp://localhost:1935/live/{stream_key}` |
| HLS | devolvido no campo `hls_url` |
| playback | devolvido no campo `url` ou `playback_url` |

## Fluxo de teste para 1 a 8 câmeras

1. Inicie os containers.
2. Abra `/docs` e crie as câmeras com `POST /api/v1/cameras`.
3. Abra as credenciais RTMP devolvidas pela API.
4. No **Mibo Smart/Mibo Cam**, apague o conteúdo anterior do campo `URL RTMP` e
   cole somente `rtmp_url`, uma única vez.
5. Em outros equipamentos com campos separados, use `rtmp_server_url` no campo servidor e
   `stream_key` no campo chave.
6. Configure o encoder para **H.264 + AAC**.
7. Se não houver câmera disponível, execute no Windows:

```powershell
.\scripts\test-streams.ps1 -Count 2
```

O script aceita de 1 a 8 streams e gera vídeo e áudio sintéticos com FFmpeg.

## Comandos de verificação

```bash
docker compose logs -f backend mediamtx
docker compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
```

Testes Python fora do container:

```bash
cd backend
python -m pip install -r requirements.txt ruff
ruff check app tests
ruff format --check app tests
pytest -q
```

Os testes marcados como `integration` precisam do conjunto Docker ativo:

```bash
pytest -q -m integration
```

## Publicação em servidor

O GitHub compartilha o código, mas não executa RTMP continuamente. Para uma URL pública é necessária uma VM/VPS Linux com IP público e portas `80`, `443` e `1935` liberadas.

Use [`DEPLOY.md`](DEPLOY.md) e `compose.prod.yml`. O conjunto público inclui Caddy com HTTPS automático e autenticação HTTP. O backend, o banco e as APIs internas não são expostos diretamente.

Para uma hora de oito câmeras a 4 Mbit/s, reserve pelo menos 25 GB úteis para gravações e margem. O consumo teórico de vídeo é aproximadamente 14,4 GB por hora; sistema, banco e variação de bitrate exigem espaço adicional.

## Regras técnicas das câmeras

- vídeo: H.264;
- áudio: AAC;
- Mibo Smart/Mibo Cam: cole somente a `rtmp_url` completa no campo `URL RTMP`;
- a URL usa o formato `rtmp://servidor:1935/live/chave`, necessário para separar
  a aplicação RTMP (`live`) da chave da câmera;
- publicação com campos separados: use `rtmp_server_url` como servidor e
  `stream_key` como chave; nunca repita a URL completa no campo da chave;
- relógio da câmera e do servidor sincronizados por NTP;
- bitrate recomendado para o beta: ajuste conforme rede e disco;
- H.265 pode ser gravado, mas não tem reprodução consistente nos navegadores deste MVP.

## Limites conscientes do beta

- um usuário/senha HTTP compartilhado no ambiente público, sem contas individuais;
- retenção global fixa em 1 hora;
- sem PTZ, análise de vídeo ou notificações push;
- sem transcodificação: a câmera deve enviar codecs compatíveis;
- gravações antigas não são recuperáveis depois da limpeza;
- dimensionamento e redundância precisam ser revistos antes de uso comercial.

O projeto implementa funcionalidades próprias. Não contém código, marca ou identidade visual proprietária de terceiros.
