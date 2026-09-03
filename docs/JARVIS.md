# Jarvis

Jarvis is your personal operating intelligence: one always-on assistant you
talk to on Telegram, by voice note or text, that knows your whole world and
acts on it. It speaks as Mary Jane, Operational Commander of your Executive
Board, and it obeys Rule Zero: the Vault is the single source of truth, so it
never quotes holdings, cash or plans from memory.

## What it knows

| Source | What Jarvis reads | What Jarvis writes |
|---|---|---|
| The Vault (finance-chief Supabase project) | identity profile, 75 agent rules, goals, portfolio summary, holdings, watchlist, decision log, session captures, memory events, ventures, content pipeline | decisions, thoughts, memories, session captures, watchlist items, pipeline items, every conversation turn |
| OrigineX Human Archives database | content ideas, episodes, citations, people, documents, scholarly flags (contested claims), competitive intel, open citation flags, declass inbox | content ideas |
| Shopify (optional) | orders and sales summary | nothing |
| Web (optional, Brave key) | current news and prices | nothing |

Jarvis never executes a trade or moves money. It logs the decision; you execute.

## Commands

1. `/brief` morning brief: portfolio, goals, last decisions, content pipeline, open flags, one action for today.
2. `/portfolio` live summary and top ten holdings, straight from the Vault, no Claude call.
3. `/goals` active goals.
4. `/rules` the binding agent rules. `/rules benefits` filters by domain.
5. `/new` fresh conversation.
6. `/close` summarise the session and save it to session_captures.
7. `/refresh` reload the live context from both databases.
8. `/voice on` or `/voice off` spoken replies.
9. `/help` the list.

Anything else, just talk. Say "remember that..." and it saves a memory. Say
"log the decision..." and it writes the decision log. Ask "what did we decide
about RDW" and it searches the log.

## Deploy on Railway, step by step

Jarvis runs as a second service in the same Railway project as the intraday
trading engine. Nothing about the trading service changes.

1. Open Telegram, message `@BotFather`, send `/newbot`, follow the two prompts, and copy the token it gives you.
2. In Railway open the existing project and click New, then GitHub Repo, and pick this repository again.
3. In the new service open Settings, find Config-as-code, and set the path to `jarvis/railway.toml`.
4. Open Variables and add the values in the table below. Only the first four are essential.
5. Click Deploy. The logs should show a box that starts with "Jarvis online as @yourbot".
6. Message your bot "hello". If it replies "Not authorised. This chat id is 12345678", add that number as `TELEGRAM_CHAT_ID` in Variables and redeploy. The bot already knows your chat id if telegram_config in the Vault is enabled.
7. Send `/brief`.

## Variables

| Variable | Needed | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | yes | console.anthropic.com |
| `TELEGRAM_BOT_TOKEN` | yes | from BotFather |
| `SUPABASE_URL` | yes | finance-chief project URL |
| `SUPABASE_SERVICE_KEY` | yes | finance-chief service-role key, never the anon key |
| `OGX_SUPABASE_URL` | for content | OrigineX project URL |
| `OGX_SUPABASE_SERVICE_KEY` | for content | OrigineX service-role key |
| `TELEGRAM_CHAT_ID` | recommended | your chat id; falls back to telegram_config in the Vault |
| `OPENAI_API_KEY` | for voice in | Whisper transcription of your voice notes |
| `ELEVENLABS_API_KEY` | for voice in/out | Scribe transcription if no OpenAI key; text-to-speech for spoken replies |
| `ELEVENLABS_VOICE_ID` | for voice out | the voice Jarvis speaks with |
| `JARVIS_MODEL` | optional | default `claude-opus-5` |
| `JARVIS_EFFORT` | optional | `low`, `medium`, `high` (default), `xhigh`, `max` |
| `JARVIS_FALLBACKS` | optional | default on: if Claude declines a request on safety grounds the API re-runs it on a fallback model inside the same call |
| `JARVIS_NAME` | optional | default `Jarvis` |
| `JARVIS_VOICE_REPLIES` | optional | default on; spoken reply after every voice note when ElevenLabs is set |
| `JARVIS_HISTORY_TURNS` | optional | turns kept in working memory, default 20 |
| `JARVIS_CONTEXT_TTL` | optional | seconds before the live snapshot refreshes, default 600 |
| `BRAVE_SEARCH_API_KEY` | optional | enables web_search |
| `SHOPIFY_SHOP_NAME`, `SHOPIFY_ACCESS_TOKEN` | optional | enables shopify_summary |

## Run it locally

```bash
pip install -r requirements.txt
cp .env.example .env      # fill in the variables above
python main.py jarvis     # or: python -m jarvis
```

## How memory works

1. Every day gets one conversation row in mj_conversations, titled "Telegram YYYY-MM-DD HH:MM". Restarts resume the same day.
2. Every user and assistant message is written to mj_messages, so nothing is lost when the container restarts.
3. Facts and preferences go to mj_semantic_memories via the remember tool and come back via recall.
4. Decisions go to decision_log and are mirrored to ai_memory_events, the same table the other AI sessions feed.
5. `/close` writes a session_captures row: summary, decisions, action items.
6. The live context (rules, goals, portfolio, pipeline, flags) is rebuilt every ten minutes and cached, so most turns reuse it at a fraction of the token cost.

## Cost

Claude Opus 5 is the default. With the persona and live context cached, a
typical turn costs a few pence. `/portfolio`, `/goals` and `/rules` cost
nothing because they read the Vault directly. Set `JARVIS_EFFORT=medium` to
trim spend on routine chat; keep `high` for investment questions.

## Security

1. Only one Telegram chat is ever answered. Every other chat gets a one-line refusal.
2. The service-role keys live only in Railway variables, never in the repo.
3. Seven Vault tables still have Row Level Security switched off, including telegram_config and t212_api_config. `supabase/migrations/20260903_jarvis_vault_rls.sql` locks them; run it in the Supabase SQL editor once you have checked that nothing of yours uses the anon key against those tables. Jarvis is unaffected because it uses the service-role key.

## Troubleshooting

1. "Jarvis cannot start. Missing: ..." means a required variable is empty.
2. "Not authorised" means the chat id does not match. Copy the number it prints into `TELEGRAM_CHAT_ID`.
3. "I can't hear voice notes yet" means no transcription key is set.
4. Replies say "the Vault has no record": the row really is not there, or the service key is wrong. Check the deploy log heartbeat line that reads "vault ok".
5. Slow first reply after a restart is the live context loading. It is cached afterwards.
