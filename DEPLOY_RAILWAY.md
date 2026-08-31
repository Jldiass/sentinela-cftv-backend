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

O Railway usa `Dockerfile.railway` automaticamente por meio de `railway.toml`.

## Variáveis

Configure no serviço:

```env
BASIC_AUTH_USER=gestor
BASIC_AUTH_PASSWORD=troque-por-uma-senha-forte
PUBLIC_HLS_BASE_URL=/hls
PUBLIC_PLAYBACK_BASE_URL=/playback
RECORD_DELETE_AFTER=1h
CAMERA_LIMIT=8
```

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

## Capacidade de gravação

O volume deve ser dimensionado pelo bitrate real. Oito câmeras a 4 Mbit/s
consomem aproximadamente 14,4 GB em uma hora, sem contar margem operacional.
O volume gratuito de 0,5 GB não comporta esse cenário e o limite de 5 GB do
plano Hobby também não sustenta uma hora completa das oito câmeras.

## Validação

1. Abra `https://DOMINIO/railway-health`; deve retornar `ok: true`.
2. Entre no painel com o usuário e senha configurados.
3. Cadastre uma câmera.
4. Cole a URL `rtmp_url` no campo personalizado do Mibo.
5. Confirme estado `unstable` e depois `online`.
6. Verifique imagem, áudio e um segmento no Histórico.
