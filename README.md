# Sentinela — backend CFTV

MVP próprio para até 8 câmeras: RTMP com áudio, HLS ao vivo, mosaico, status, gravação 24h, retenção de 7 dias, busca temporal e eventos com pré/pós-alarme.

O backend é a fonte oficial do projeto. O contrato está em [`BACKEND_API.md`](BACKEND_API.md), o handoff está em [`FRONTEND_HANDOFF.md`](FRONTEND_HANDOFF.md) e a publicação pública está em [`DEPLOY.md`](DEPLOY.md). A tela incluída é apenas um demonstrador.

## Componentes

- **MediaMTX 1.20.1:** ingestão RTMP, HLS, gravação fMP4 e playback.
- **FastAPI + PostgreSQL:** cadastro, chaves individuais, estado, gravações e eventos.
- **Frontend web:** mosaico, cadastro e histórico, servido pelo backend.
- **FFmpeg:** gerador opcional de streams de teste com vídeo e áudio.

## Início rápido

1. Copie `.env.example` para `.env` e troque a senha do banco.
2. Execute `docker compose up --build -d`.
3. Abra `http://localhost:8000`.
4. Cadastre de 1 a 8 câmeras e copie a URL RTMP exibida.
5. Configure a câmera/encoder para publicar H.264 + AAC nessa URL. A chave já faz parte do caminho.

Verificações:

- API e tela: `http://localhost:8000`
- documentação da API: `http://localhost:8000/docs`
- saúde: `http://localhost:8000/health`
- logs: `docker compose logs -f backend mediamtx`

## Servidor público

O arquivo `compose.prod.yml` sobe o conjunto completo em uma VPS com persistência, HTTPS automático e autenticação HTTP. Ele publica somente `80/443` para o painel/API/mídias e `1935` para ingestão RTMP. Consulte [`DEPLOY.md`](DEPLOY.md) antes de apontar as câmeras.

As URLs públicas não ficam fixas no código. O backend usa `PUBLIC_RTMP_BASE_URL`, `PUBLIC_HLS_BASE_URL` e `PUBLIC_PLAYBACK_BASE_URL`; por isso o mesmo código funciona localmente, em homologação e em produção.

## Teste sem câmera física

Requer FFmpeg instalado no Windows. Depois de cadastrar as câmeras, execute:

```powershell
.\scripts\test-streams.ps1 -Count 2
```

Cada processo publica uma mira de teste diferente com tom de áudio. Aceita de 1 a 8 streams. Para encerrar, finalize os processos `ffmpeg` iniciados pelo teste.

## Pré-alarme

O MediaMTX grava segmentos de 10 segundos continuamente. Ao receber um evento, a API guarda o instante e calcula uma janela que começa `pre_alarm_seconds` antes e termina `post_alarm_seconds` depois. Exemplo:

```http
POST /api/v1/cameras/1/events
Content-Type: application/json

{"kind":"zona-03","note":"Movimento na entrada"}
```

O item aparece em Histórico com uma URL de playback que agrega os segmentos da janela. A gravação já existe antes do evento; portanto o pré-alarme não depende de manter vídeo em memória.

## Resgate e retenção

O endpoint `GET /api/v1/cameras/{id}/recordings?start=...&end=...` consulta o playback do MediaMTX. A exclusão é automática após 7 dias (`recordDeleteAfter: 7d`). O campo de retenção por câmera já faz parte do cadastro para evolução; neste MVP a política efetiva é global em 7 dias, conforme o escopo.

## Observações de produção

A configuração pública já inclui TLS/reverse proxy, proteção HTTP e autorização de publicação por chave. Ainda é obrigatório monitorar disco, fazer backups e testar capacidade. Status `online` vem da API de caminhos ativos do MediaMTX; `offline` significa sem publicador. Um canal recém-conectado aparece como `instável` por 20 segundos, uma janela conservadora de estabilização. Para produto comercial com vários operadores, evolua para contas individuais, auditoria e URLs de mídia assinadas.

## Portas

| Porta | Uso |
|---:|---|
| 8000 | interface e API |
| 1935 | ingestão RTMP |
| 8888 | HLS ao vivo |
| 8889 | WebRTC (habilitado para evolução) |
| 9996 | playback de gravações |
