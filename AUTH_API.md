# Autenticação — contrato para o frontend

Base da API: `/api/v1`. Todos os corpos e respostas usam JSON, exceto o
`refresh_token`, que fica em cookie `HttpOnly` e não é acessível pelo JavaScript.

## Fluxo recomendado

1. Faça registro ou login.
2. Guarde `access_token` somente em memória (estado da aplicação).
3. Envie `Authorization: Bearer {access_token}` nas rotas protegidas.
4. Quando uma requisição retornar `401`, chame `/auth/refresh` uma única vez e
   repita a requisição original com o novo access token.
5. Sempre use `credentials: "include"` em login, registro, refresh e logout.
6. Ao recarregar a página, chame `/auth/refresh` para reconstruir a sessão.
7. Nunca grave access ou refresh token em `localStorage` ou `sessionStorage`.

O access token expira em 15 minutos. O refresh token expira em 30 dias, é
rotacionado em todo uso e somente seu hash HMAC-SHA256 fica no banco. Reutilizar
um refresh token antigo revoga toda a família daquela sessão.

## Endpoints

| Método | Endpoint | Autenticação | Uso |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | pública | cadastrar usuário e iniciar sessão |
| `POST` | `/api/v1/auth/login` | pública | autenticar e iniciar sessão |
| `POST` | `/api/v1/auth/refresh` | cookie | renovar access e refresh token |
| `POST` | `/api/v1/auth/logout` | cookie | encerrar a sessão atual |
| `POST` | `/api/v1/auth/logout-all` | Bearer | encerrar todas as sessões do usuário |
| `GET` | `/api/v1/auth/me` | Bearer | obter o usuário autenticado |
| `POST` | `/api/v1/auth/forgot-password` | pública | solicitar recuperação por e-mail |
| `POST` | `/api/v1/auth/reset-password` | token de recuperação | definir uma nova senha |
| `POST` | `/api/v1/auth/change-password` | Bearer | alterar senha sabendo a atual |

### `POST /api/v1/auth/register`

```json
{
  "email": "operador@empresa.com",
  "full_name": "Nome do Operador",
  "password": "uma-senha-com-12-ou-mais"
}
```

Resposta `201`:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "email": "operador@empresa.com",
    "full_name": "Nome do Operador",
    "is_active": true,
    "created_at": "2026-08-30T15:00:00Z",
    "last_login_at": null
  }
}
```

Conflito de e-mail retorna `409`. E-mail inválido, senha menor que 12 caracteres
ou campos extras retornam `422`.

### `POST /api/v1/auth/login`

```json
{
  "email": "operador@empresa.com",
  "password": "uma-senha-com-12-ou-mais"
}
```

A resposta `200` tem o mesmo formato do registro. Credenciais inválidas retornam
`401`. Após cinco erros consecutivos, a conta fica bloqueada por 15 minutos e a
API retorna `429` com o cabeçalho `Retry-After`.

### `POST /api/v1/auth/refresh`

Sem corpo. O navegador envia o cookie automaticamente:

```ts
const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
  method: "POST",
  credentials: "include",
});
```

Resposta `200`: novo objeto de autenticação. Token ausente, vencido, revogado ou
reutilizado retorna `401` e limpa o cookie.

### `GET /api/v1/auth/me`

```ts
const response = await fetch(`${API_URL}/api/v1/auth/me`, {
  headers: { Authorization: `Bearer ${accessToken}` },
});
```

Resposta `200`: objeto `user`. Token inválido ou expirado retorna `401`.

### `POST /api/v1/auth/logout`

Sem corpo. Envie `credentials: "include"`. Revoga o refresh token atual e limpa
o cookie. Resposta `200`:

```json
{ "message": "Sessão encerrada" }
```

### `POST /api/v1/auth/logout-all`

Envie o Bearer token. Revoga todos os refresh tokens e invalida imediatamente
todos os access tokens existentes do usuário.

### `POST /api/v1/auth/forgot-password`

```json
{ "email": "operador@empresa.com" }
```

A resposta é sempre `200` e igual para e-mail existente ou inexistente, evitando
exposição da lista de usuários:

```json
{
  "message": "Se o e-mail estiver cadastrado, enviaremos as instruções de recuperação.",
  "debug_reset_token": null
}
```

O backend limita a três solicitações por usuário por hora. Em produção,
`AUTH_DEBUG_RETURN_RESET_TOKEN` precisa permanecer `false` e o envio deve ser
configurado por SMTP.

### `POST /api/v1/auth/reset-password`

```json
{
  "token": "token-recebido-no-link-do-email",
  "new_password": "uma-nova-senha-com-12-ou-mais"
}
```

O token expira em 30 minutos, é de uso único e somente seu hash fica no banco.
Ao redefinir a senha, todas as sessões anteriores são invalidadas. Token inválido,
usado ou expirado retorna `400`.

### `POST /api/v1/auth/change-password`

Requer Bearer token:

```json
{
  "current_password": "senha-atual",
  "new_password": "uma-nova-senha-com-12-ou-mais"
}
```

Ao concluir, todas as sessões são encerradas e o frontend deve redirecionar para
o login.

## Exemplo de cliente TypeScript

```ts
export type AuthSession = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: {
    id: number;
    email: string;
    full_name: string;
    is_active: boolean;
    created_at: string;
    last_login_at: string | null;
  };
};

export async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw await response.json();
  return (await response.json()) as AuthSession;
}
```

## Recuperação de senha em produção

Configure estas variáveis no servidor:

```env
PASSWORD_RESET_FRONTEND_URL=https://seu-dominio/reset-password
SMTP_HOST=smtp.seu-provedor.com
SMTP_PORT=587
SMTP_USERNAME=usuario
SMTP_PASSWORD=senha-ou-api-key
SMTP_FROM=no-reply@seu-dominio.com
AUTH_DEBUG_RETURN_RESET_TOKEN=false
```

O frontend deve ler `token` da URL, renderizar o formulário de nova senha e
enviar o valor para `/auth/reset-password`. A página deve definir
`Referrer-Policy: no-referrer` para não vazar o token a sites externos.

## Segurança implementada

- senha armazenada como hash Argon2id com salt, nunca em texto puro;
- SQLAlchemy ORM com parâmetros, sem interpolação de entradas em SQL;
- resposta genérica na recuperação de senha;
- tokens de recuperação opacos, aleatórios, expirados e de uso único;
- JWT com assinatura, `issuer`, `audience`, `exp`, `nbf`, `jti` e versão de sessão;
- refresh token opaco, rotativo, revogável e salvo apenas como digest;
- cookie `HttpOnly`, `SameSite=Strict`, caminho restrito e `Secure` em produção;
- bloqueio temporário após tentativas repetidas de login;
- mudança/redefinição de senha invalida todas as sessões anteriores;
- respostas recusam campos JSON extras e validam formato e tamanho.

Em produção, mantenha frontend e API no mesmo domínio, use somente HTTPS,
configure `AUTH_COOKIE_SECURE=true`, mantenha o segredo fora do Git e aplique
limite de requisições por IP no proxy/CDN.
