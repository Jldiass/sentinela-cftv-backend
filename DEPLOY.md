# Publicação em servidor

Esta configuração executa o backend, PostgreSQL, MediaMTX e proxy HTTPS em um servidor Linux público. O vídeo gravado e o banco ficam em volumes persistentes do Docker. O Caddy emite e renova o certificado TLS automaticamente.

## Infraestrutura necessária

- VPS Linux com IP público fixo, Docker Engine e Docker Compose;
- domínio ou subdomínio com registro DNS `A` apontando para o IP da VPS;
- portas TCP `80`, `443` e `1935` liberadas no firewall;
- disco dimensionado para uma hora de gravação de até oito câmeras.

Como referência, oito câmeras a 4 Mbit/s consomem aproximadamente 14,4 GB por hora. Reserve pelo menos 25 GB para gravações, além do espaço do sistema, banco e imagens Docker.

Não use hospedagem serverless para este serviço. RTMP contínuo, FFmpeg/MediaMTX e gravações exigem um servidor persistente. Para o primeiro ambiente, uma VPS Ubuntu é a opção mais simples.

## Dimensionamento recomendado

O backend apenas remuxa H.264/AAC para HLS; ele não transcodifica. Para até oito canais, comece com 4 vCPU, 8 GB de RAM, porta de pelo menos 200 Mbit/s e armazenamento útil conforme o bitrate:

| Bitrate por câmera | Uma hora / 8 câmeras | Espaço recomendado para gravações |
|---:|---:|---:|
| 1 Mbit/s | ~3,6 GB | 8 GB |
| 2 Mbit/s | ~7,2 GB | 15 GB |
| 4 Mbit/s | ~14,4 GB | 25 GB |
| 6 Mbit/s | ~21,6 GB | 35 GB |
| 8 Mbit/s | ~28,8 GB | 45 GB |

Use H.264 + AAC diretamente na câmera. Se houver transcodificação, o dimensionamento de CPU muda bastante.

## Primeira publicação

```bash
git clone URL_DO_REPOSITORIO
cd sentinela-cftv-backend
cp .env.production.example .env.production
```

Para o beta, use `cp .env.free-beta.example .env.production`. A configuração mantém até oito cadastros e uma janela móvel de uma hora. A API devolve `effective_retention_hours: 1` para o frontend exibir o valor verdadeiro.

Em uma VPS Ubuntu nova, o script abaixo instala Docker, configura o firewall e cria as pastas persistentes:

```bash
sudo ./scripts/prepare-ubuntu-server.sh
```

Gere o hash da senha que protegerá painel, API, HLS e playback:

```bash
docker run --rm caddy:2.10-alpine caddy hash-password --plaintext 'SENHA_FORTE'
```

Edite `.env.production`. Informe domínio, e-mail, senha alfanumérica forte do PostgreSQL, usuário e o hash gerado. Mantenha o hash entre aspas simples. Depois execute:

```bash
./scripts/deploy-production.sh
```

Acesse `https://SEU_DOMINIO/docs`. O navegador solicitará o usuário e a senha definidos no Caddy.

## Endereços públicos

- API: `https://SEU_DOMINIO/api/v1`
- Swagger: `https://SEU_DOMINIO/docs`
- saúde: `https://SEU_DOMINIO/health`
- RTMP: `rtmp://SEU_DOMINIO:1935/{stream_key}`
- HLS e playback: URLs completas devolvidas pela API

O frontend deve definir `VITE_API_URL=https://SEU_DOMINIO/api/v1`. Se for hospedado em outro domínio, inclua esse endereço em `CORS_ORIGINS` e mantenha o acesso protegido. Para a primeira entrega, servir frontend e backend no mesmo domínio simplifica autenticação e reprodução HLS.

## Atualização

```bash
git pull --ff-only
./scripts/deploy-production.sh
```

## Backup e operação

```bash
docker compose --env-file .env.production -f compose.prod.yml logs -f backend mediamtx caddy
docker compose --env-file .env.production -f compose.prod.yml exec -T postgres pg_dump -U cftv cftv > backup-cftv.sql
```

Monitore uso de disco. A retenção apaga segmentos com mais de uma hora, mas picos de bitrate, streams interrompidos e arquivos temporários exigem margem. Faça backup do PostgreSQL e teste restauração antes do uso operacional.

## Limite de segurança do MVP

O HTTPS e a autenticação HTTP impedem acesso anônimo ao painel e às mídias. A chave RTMP individual autoriza publicação. Para produto comercial com vários usuários, a evolução correta é implementar contas, perfis, auditoria, URLs de mídia assinadas e armazenamento externo/replicado.
