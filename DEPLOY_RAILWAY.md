# Publicação no Railway

Este projeto possui uma imagem única para Railway com:

- painel React;
- FastAPI;
- MediaMTX;
- ingestão RTMP pública por TCP Proxy;
- HLS e playback pelo mesmo domínio HTTPS;
- gravação em volume persistente;
- autenticação HTTP do painel.

## Recursos necessários

1. Um serviço criado a partir deste repositório GitHub.
2. Domínio HTTP gerado pelo Railway para a porta `8080`.
3. TCP Proxy gerado pelo Railway para a porta interna `1935`.
4. Volume montado em `/data`.

O Railway detecta o `Dockerfile` na raiz automaticamente. `Dockerfile.railway`
permanece como cópia explícita para referência e compatibilidade.

## Variáveis

Configure no serviço:

```env
BASIC_AUTH_USER=gestor
BASIC_AUTH_PASSWORD=troque-por-uma-senha-forte
AUTH_JWT_SECRET=gere-uma-chave-aleatoria-com-pelo-menos-32-caracteres
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=strict
AUTH_DEBUG_RETURN_RESET_TOKEN=false
PASSWORD_RESET_FRONTEND_URL=https://SEU-DOMINIO/reset-password
PUBLIC_HLS_BASE_URL=/hls
PUBLIC_PLAYBACK_BASE_URL=/playback
RECORD_DELETE_AFTER=1h
CAMERA_LIMIT=8
STATUS_POLL_SECONDS=10
```

Para ativar e-mail de recuperação de senha, configure também `SMTP_HOST`,
`SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` e `SMTP_FROM`. Não habilite
`AUTH_DEBUG_RETURN_RESET_TOKEN` em ambiente público.

Depois de gerar o TCP Proxy, o Railway fornece um endereço semelhante a
`shuttle.proxy.rlwy.net:15140`. Acrescente:

```env
PUBLIC_RTMP_BASE_URL=rtmp://shuttle.proxy.rlwy.net:15140
```

A API então gera URLs Mibo no formato:

```text
rtmp://shuttle.proxy.rlwy.net:15140/live/cam-chave-individual
```

## Banco de dados

Sem `DATABASE_URL`, o beta usa SQLite em `/data/malupe-cam.db`. Como `/data` é
um volume Railway, os cadastros persistem entre deploys. Para PostgreSQL,
adicione o serviço PostgreSQL do Railway e configure `DATABASE_URL` com a URL
fornecida pela plataforma.

Antes de iniciar a API, a imagem executa `alembic upgrade head`. Assim as tabelas
de mosaicos, perfis, permissões, auditoria e conectividade são criadas sem apagar
as câmeras e eventos que já existem no volume.

## Capacidade de gravação

O volume deve ser dimensionado pelo bitrate real. Oito câmeras a 4 Mbit/s
consomem aproximadamente 14,4 GB em uma hora, sem contar margem operacional.
O volume gratuito de 0,5 GB não comporta esse cenário e o limite de 5 GB do
plano Hobby também não sustenta uma hora completa das oito câmeras.

### Gravação em Cloudflare R2 (recomendado para não depender do volume)

Configure estas variáveis para que cada segmento gravado seja enviado ao R2
e apagado do disco local logo em seguida (o volume passa a guardar só um
buffer de 10 minutos, não a hora inteira):

```env
R2_ACCOUNT_ID=seu-account-id-cloudflare
R2_ACCESS_KEY_ID=gerado-em-r2-manage-api-tokens
R2_SECRET_ACCESS_KEY=gerado-em-r2-manage-api-tokens
R2_BUCKET_NAME=malupe-cam-recordings
```

Custo esperado: R2 tem 10 GB de armazenamento e 1 milhão de operações de
escrita grátis por mês, sem cobrar saída (egress). Com 8 câmeras a 4 Mbit/s
e segmentos de 60s (configurado em `mediamtx/railway.yml`), o uso fica em
torno de 14 GB armazenados (janela móvel de 1h) e ~345 mil escritas/mês —
dentro ou muito próximo do nível grátis; o excedente de armazenamento custa
centavos de dólar por mês. Sem essas variáveis configuradas, o sistema
continua gravando só no volume local, como antes.

## Validação

1. Abra `https://DOMINIO/railway-health`; deve retornar `ok: true`.
2. Entre na proteção HTTP com `BASIC_AUTH_USER` e `BASIC_AUTH_PASSWORD`.
3. No primeiro deploy, crie o administrador por `POST /api/v1/auth/register`.
4. Entre na aplicação e cadastre uma câmera.
4. Cole a URL `rtmp_url` no campo personalizado do Mibo.
5. Confirme estado `unstable` e depois `online`.
6. Verifique imagem, áudio e um segmento no Histórico.
