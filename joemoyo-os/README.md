# JoeMoyo OS 🧠

Your AI-powered personal operating system — content, money, and every AI model, unified in one
dynamic web dashboard. Built with Next.js + Supabase, deployable free on Vercel.

## Modules

| Module | Status | What it does |
|---|---|---|
| 🧠 **AI Hub** | ✅ Live | One prompt → Claude + ChatGPT + Perplexity, answers side by side |
| 🎬 **Content Studio** | Phase 2 | Scripts, thumbnail concepts, content calendar |
| 📈 **Investing** | Phase 3 | Portfolio, market data, AI alerts & buy/sell suggestions |
| 📡 **Social** | Phase 4 | YouTube + socials analytics, draft & schedule posts |

The **Vault** (your Supabase project) is the shared memory every module reads and writes.

## Run it locally

```bash
cd joemoyo-os
npm install
cp .env.example .env.local   # then fill in your keys
npm run dev                  # http://localhost:3000
```

You only need **one** AI key to start — the AI Hub shows which providers are live in the top bar.

## Deploy (free, accessible on your phone)

1. Push this repo to GitHub (already done).
2. Import it at [vercel.com/new](https://vercel.com/new), set the root directory to `joemoyo-os`.
3. Add the same env vars from `.env.example` in Vercel's project settings.
4. Deploy → open the URL on any device. Add it to your home screen for an app feel.

## Architecture

```
app/
  page.tsx            Dashboard home
  hub/                AI Hub (working multi-model chat)
  studio|investing|social/   Module shells (wired in later phases)
  api/chat            Fan-out endpoint → all selected providers
  api/health          Reports which keys/vault are configured
lib/
  ai/providers.ts     Claude / OpenAI / Perplexity behind one interface
  supabase/server.ts  The Vault client
components/            Sidebar, status bar, cards, chat UI
```

## Security

- Secrets live in `.env.local` (git-ignored) or Vercel env vars — never in code.
- The Supabase **service-role key** is used server-side only.
- Investing never auto-trades: it only alerts and suggests.
