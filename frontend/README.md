# Malupe Cam — Front-end

Painel operacional para monitoramento CFTV. A aplicação consome a API Malupe Cam para administrar câmeras, acompanhar canais HLS ao vivo, consultar o histórico de gravações, registrar eventos e verificar a saúde da infraestrutura.

## Recursos

- CRUD de até oito câmeras, com habilitação, desabilitação, credenciais RTMP e rotação de chave;
- mosaico de vídeo HLS com estados `online`, `unstable` e `offline`;
- histórico limitado à retenção efetiva informada pelo backend;
- criação, consulta e remoção de eventos com pré/pós-alarme;
- painel de saúde para PostgreSQL e MediaMTX;
- tema escuro operacional como padrão e alternador persistente para modo claro.
- login real com access token somente em memória e refresh token em cookie `HttpOnly`;
- primeiro acesso, recuperação e redefinição de senha;
- rotas e ações condicionadas pelas permissões devolvidas pela API;
- mosaicos persistentes de 1 a 36 posições com associação de usuários, perfis e câmeras;
- gestão de usuários, perfis e permissões;
- resumo e histórico de conectividade online, instável e offline.

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

## Fluxo de autenticação

1. Em uma instalação vazia, abra `/register` para criar o único administrador inicial.
2. Depois disso, novas contas são criadas em **Usuários** por quem possui `users.manage`.
3. O access token fica somente em memória. O refresh token nunca é lido pelo JavaScript.
4. Ao receber `401`, o cliente compartilha uma única tentativa de `/auth/refresh` e repete a chamada.
5. `403` mantém a sessão e mostra que o perfil não permite a operação.

Principais permissões usadas na navegação: `overview.read`, `mosaics.read`,
`mosaics.manage`, `cameras.read`, `cameras.manage`, `events.read`,
`events.manage`, `reports.read`, `users.manage`, `permissions.manage` e
`system.health.read`.

## Contratos consumidos

| Área          | Endpoints                                                        |
| ------------- | ---------------------------------------------------------------- |
| Sessão        | `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`       |
| Recuperação   | `/auth/forgot-password`, `/auth/reset-password`                  |
| Câmeras       | `/cameras`, `/cameras/{id}/stream`, gravações e rotação de chave |
| Mosaicos      | `/mosaics`, `/mosaics/{id}`, `/mosaics/{id}/view`                |
| Acesso        | `/users`, `/roles`, `/permissions`                               |
| Conectividade | `/camera-status/summary`, `/camera-status/history`               |

O cadastro e a listagem comuns de câmeras não recebem chave nem URL RTMP. Essas
credenciais são buscadas separadamente por `/cameras/{id}/stream`, que exige
`cameras.manage`.

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
