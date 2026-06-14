# Trading Bot Builder — Claude Skill

A Claude Code **Skill** that builds a complete automated **paper-trading** bot on
Alpaca, end to end: SMA trend strategy with a trailing-stop exit, backtesting +
walk-forward validation, an intraday engine, a Streamlit dashboard, GitHub
Actions automation, a self-logging journal with an AI coach, Supabase durable
memory, and a pass/fail scorecard.

> ⚠️ Educational, **paper trading only**, not financial advice. See `NOTICE.md`.

## What's inside
```
trading-bot-builder/
├── SKILL.md              # the guided build (read this first)
├── references/           # deep dives per phase + lessons-learned.md
├── assets/templates/     # genericized, credential-free code to drop in
│   ├── tools/  agents/  dashboard/  config/  main.py  requirements.txt
│   ├── .env.example  .github/workflows/  supabase/migrations/
├── scripts/package_skill.sh   # build the distributable zip
├── LICENSE.md  NOTICE.md
└── README.md
```

## Use it as a skill
Copy this folder into `~/.claude/skills/` (or keep it in a repo's
`.claude/skills/`). Then ask Claude something like *"build me an Alpaca
paper-trading bot"* and it will follow `SKILL.md`.

## Use the templates directly
1. Copy `assets/templates/*` into a fresh repo.
2. `cp .env.example .env` and add your Alpaca **paper** keys.
3. `pip install -r requirements.txt`
4. `python main.py overview` then `python main.py autotrade --symbols SPY,QQQ --once --dry-run`
5. Backtest, deploy the dashboard, wire the workflows — `SKILL.md` has the order.

## Package to share/sell
```bash
bash scripts/package_skill.sh      # -> dist/trading-bot-builder-skill.zip
```

Built from a real, working system — `references/lessons-learned.md` is where the
hard-won knowledge lives.
