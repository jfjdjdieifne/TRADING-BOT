# Michael ICT Academy

Repositório do projeto Michael ICT Academy (Next.js + TypeScript).

## Visão geral
Aplicação web construída com Next.js, Supabase para backend/auth, e Stripe para pagamentos. Este README descreve como configurar, rodar localmente, e como funciona o CI básico.

## Pré-requisitos
- Node.js 18+ (recomendado)
- npm (ou pnpm/yarn)
- Conta Supabase
- Conta Stripe (para pagamentos)

## Instalação (local)
1. Clone o repositório:
   git clone https://github.com/Mike061crypto/michael-ict-academy.git
   cd michael-ict-academy

2. Instale dependências:
   npm ci

3. Crie um arquivo `.env.local` baseado em `.env.example` e preencha as variáveis de ambiente.

4. Rodar em desenvolvimento:
   npm run dev

5. Build de produção (local):
   npm run build
   npm start

## Variáveis de ambiente
Preencha `.env.local` com as chaves apropriadas. Principais chaves (já estão no `.env.example`):
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- NEXT_PUBLIC_API_URL / NEXT_PUBLIC_APP_URL
- NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY / STRIPE_SECRET_KEY / STRIPE_WEBHOOK_SECRET
- SENDGRID_API_KEY / SENDGRID_FROM_EMAIL

Não comite chaves reais no repositório.

## Scripts úteis
- npm run dev — roda o app em modo desenvolvimento
- npm run build — cria o build de produção
- npm start — inicia o servidor de produção (após build)
- npm run lint — executa ESLint
- npm test — executa testes (se houver)

> Observação: adapte os nomes dos scripts se o package.json usar outros nomes.

## CI (GitHub Actions)
O repositório inclui um workflow de CI que executa em pushes e pull requests nas branches principais. O job faz:
- instalar dependências (npm ci)
- rodar lint
- rodar typecheck (npx tsc --noEmit)
- rodar testes (npm test)
- rodar build (npm run build)

Se quiser deploy automático, recomendo integrar com Vercel (conectar repositório e adicionar variáveis de ambiente no painel do Vercel) ou configurar um job de deploy no GitHub Actions.

## Deploy
Recomendado: Vercel (Next.js suportado nativamente). Alternativas: Netlify, AWS, DigitalOcean App Platform.

Passos gerais (Vercel):
1. Importar repositório no painel do Vercel.
2. Definir variáveis de ambiente (provisionadas em Settings → Environment Variables).
3. Deploy automático em pushes para `main` ou via Preview em PRs.

## Observability e produção
- Configure um Sentry/LogRocket se quiser capturar erros em produção.
- Configure backups do Supabase e alertas.

## Contribuição
1. Abra uma issue descrevendo a alteração.
2. Crie uma branch com um nome descritivo.
3. Abra um Pull Request apontando para `main`.

## Próximos passos que eu posso ajudar a automatizar
- Adicionar workflows de deploy automático (Vercel/Netlify).
- Criar templates de testes/e2e (Playwright/Cypress).
- Gerar issues com o checklist de pré-lançamento.


---

Michael ICT Academy • Criado por @Mike061crypto
