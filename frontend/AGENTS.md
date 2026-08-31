# Malupe Cam — regras de trabalho

- A interface é uma central operacional de CFTV: visual escuro, técnico, sóbrio e centrado em vídeo e estado operacional. Não introduza padrões de chat, gradientes decorativos, textos promocionais, ilustrações abstratas ou estética de produto de IA.
- Consuma exclusivamente o contrato público do FastAPI. URLs de RTMP, HLS e playback sempre vêm da API; nunca monte URLs a partir de `stream_key` e nunca exponha portas administrativas do MediaMTX.
- `VITE_API_URL` é a única origem da URL da API. Componentes não podem conhecer `localhost`.
- A retenção é global e deve ser exibida com `effective_retention_hours`; não ofereça configuração de retenção por câmera nem prometa histórico fora dessa janela.
- HLS inicia mudo, usa HLS nativo quando disponível e `hls.js` nos demais navegadores. Destrua instâncias ao desmontar e não recrie player quando a URL não mudar.
- Trate estados `online`, `unstable` e `offline`, e erros HTTP 404, 409, 422 e 503 com mensagens acionáveis em português.
- Antes de concluir alterações, execute `npm run lint`, `npm run test` e `npm run build`. Não altere o backend para compensar um problema de interface sem solicitação explícita.
