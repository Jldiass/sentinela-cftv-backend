# Malupe Cam — Front-end

Painel operacional para monitoramento CFTV. A aplicação consome a API Malupe Cam para administrar câmeras, acompanhar canais HLS ao vivo, consultar o histórico de gravações, registrar eventos e verificar a saúde da infraestrutura.

## Recursos

- CRUD de até oito câmeras, com habilitação, desabilitação, credenciais RTMP e rotação de chave;
- mosaico de vídeo HLS com estados `online`, `unstable` e `offline`;
- histórico limitado à retenção efetiva informada pelo backend;
- criação, consulta e remoção de eventos com pré/pós-alarme;
- painel de saúde para PostgreSQL e MediaMTX;
- tema escuro operacional como padrão e alternador persistente para modo claro.

## Pré-requisitos

- Node.js 20 ou superior;
- npm 10 ou superior;
- backend Malupe Cam ativo localmente ou em um ambiente acessível.

## Instalação e execução

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Por padrão, o Vite publica a aplicação em `http://localhost:5173`.

## Configuração

Defina a URL base pública da API em `.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

O frontend deriva o endpoint de saúde da mesma origem (`/health`). Não coloque URLs de HLS, RTMP ou playback no código: elas são devolvidas pelo backend em cada resposta.

Para iniciar o backend localmente:

```powershell
Set-Location ..\sentinela-cftv-backend
Copy-Item .env.example .env
docker compose up --build -d
```

Swagger estará disponível em `http://localhost:8000/docs`.

## Comandos

| Comando                | Finalidade                                        |
| ---------------------- | ------------------------------------------------- |
| `npm run dev`          | Inicia o servidor de desenvolvimento.             |
| `npm run build`        | Gera o build de produção em `dist/`.              |
| `npm run lint`         | Executa o ESLint.                                 |
| `npm run test`         | Executa testes unitários com Vitest.              |
| `npm run format`       | Formata todos os arquivos com Prettier.           |
| `npm run format:check` | Verifica a formatação sem alterar arquivos.       |
| `npm run test:e2e`     | Executa os cenários Playwright com backend ativo. |

Antes da primeira execução E2E, instale o navegador de teste:

```powershell
npx playwright install chromium
```

## Diretrizes de interface

O produto é uma central operacional de CFTV. O tema escuro é o padrão; o operador pode alternar para o tema claro no rodapé da sidebar, e a escolha fica salva no navegador. A aplicação evita padrões visuais de chat ou IA e usa cores de estado apenas para comunicação operacional.

As regras de desenvolvimento e consumo do contrato da API estão em [AGENTS.md](AGENTS.md).
