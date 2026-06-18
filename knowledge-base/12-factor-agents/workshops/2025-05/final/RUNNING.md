# Running the 12-Factor reference agent

This is the completed reference agent from the HumanLayer 12-factor-agents
workshop (`workshops/2025-05/final`). It's a small calculator agent that
demonstrates the 12-factor pattern: an LLM decides the next step
(add/subtract/multiply/divide, ask a human, or finish), built on
[BAML](https://docs.boundaryml.com).

## In-house config

We wired this to **Anthropic Claude** to match the JoeMoyo stack:
- `baml_src/agent.baml` → `DetermineNextStep` uses `client CustomSonnet`
- `baml_src/clients.baml` → `CustomSonnet` uses model `claude-sonnet-4-6` with `env.ANTHROPIC_API_KEY`

## Prerequisites
- Node.js 18+ (tested on v22)
- `ANTHROPIC_API_KEY` available in the environment (a secret — never commit it)

## Setup (one time)
```bash
cd knowledge-base/12-factor-agents/workshops/2025-05/final
npm install
npx baml-cli generate --from baml_src   # generates the gitignored baml_client/
```

## Run (CLI)
```bash
export ANTHROPIC_API_KEY=sk-ant-...      # if not already in your env
npm run dev -- "can you multiply 3 and 4, then add 12?"
```
The agent loops, calling Claude to pick each step, and prints the final answer.
If it needs clarification it will prompt you on the command line.

## Run (HTTP server)
```bash
npm run dev          # with src/index.ts pointed at the server, or run server.ts
```
See `src/server.ts` for the `/thread` endpoints.

## Optional: human-in-the-loop approvals
Set `HUMANLAYER_API_KEY` and `HUMANLAYER_EMAIL` to route clarifications and
`divide` approvals through email via HumanLayer (see `src/cli.ts`).

## Notes
- `node_modules/` and `baml_client/` are gitignored — regenerate with the setup
  steps above after cloning.
- The default `client "openai/gpt-4o"` from upstream was changed to `CustomSonnet`.
