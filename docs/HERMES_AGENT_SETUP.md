# Hermes Agent — Setup Notes

*What Hermes Agent is, why it cannot run inside a Claude Code web session, and
exactly how to install and configure it on your own machine.*

**Prepared:** 24 August 2026 · **Applies to:** Hermes Agent by Nous Research (MIT licensed)

---

## What this is

Hermes Agent is an open-source AI agent built by Nous Research. Its distinguishing
claim is a built-in learning loop: it writes its own skills from experience,
refines them as it uses them, prompts itself to persist what it has learned,
searches back through its own past conversations, and gradually builds a model of
who you are that carries across sessions.

That last part is the whole point, and it is worth holding onto, because it
determines where the agent can sensibly live. An agent whose value accumulates
over time needs somewhere permanent to accumulate it.

---

## Why it cannot run in a Claude Code web session

Two separate blockers, either of which would be enough on its own.

**The domain is blocked.** Outbound traffic from a Claude Code web session goes
through a policy-enforcing egress proxy. `hermes-agent.nousresearch.com` is not
on the allowed list, so the proxy answers `403` to the CONNECT and the installer
never downloads. This is an organisation-level network rule and is not something
to work around.

**The container is disposable.** Even setting the network aside, a web session
runs in an ephemeral container that is reclaimed once the session goes idle.
Everything inside it goes with it — the install, the accumulated memory, the
learned skills. You would be throwing away the one feature you installed it for,
every single time.

So: install it on a machine you keep. A laptop, a desktop, or a small always-on
VPS if you want it reachable from your phone via one of the messaging gateways.

---

## Before you start

On macOS and Linux the only hard prerequisite is **Git**. On Linux, also make
sure `curl` and `xz-utils` are present. You do not need to install Python,
Node.js, ripgrep or ffmpeg by hand — the installer pulls down everything it
needs, clones the repo, builds a virtual environment, puts a global `hermes`
command on your PATH, and walks you through picking an LLM provider.

On Windows the installer is even more self-contained: it bundles Python 3.11,
Node.js, ripgrep, ffmpeg and a portable Git Bash (a roughly 45 MB MinGit), and
it does not require administrator access.

---

## Installing

### macOS, Linux, WSL2

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc
hermes
```

### Windows (PowerShell)

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

### Reading the script before you run it

Both of the commands above pipe a remote script straight into an interpreter,
which means whatever that script contains executes with your user's permissions
the moment it lands. The project is reputable and MIT licensed, but the safer
habit — and the one worth keeping for every `curl | bash` installer you ever
meet, not just this one — is to separate the download from the execution:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o hermes-install.sh
less hermes-install.sh          # read it, satisfy yourself, then:
bash hermes-install.sh
```

---

## First run

Once installed, run the setup wizard:

```bash
hermes setup --portal
```

The `--portal` flag routes you through Nous Portal, where a single OAuth
authorisation covers both a model and all four Tool Gateway tools — web search,
image generation, text-to-speech, and the browser. If you would rather bring
your own provider, `hermes model` lets you point it at OpenRouter, OpenAI,
Anthropic, or a self-hosted endpoint instead; the agent is model-agnostic and
switching providers does not require touching any code.

---

## Command reference

| What you want | Command |
|---|---|
| Start chatting | `hermes` |
| Full setup wizard | `hermes setup` |
| Configure or switch model provider | `hermes model` |
| Set up messaging gateways | `hermes gateway` |
| Diagnose a broken install | `hermes doctor` |
| Migrate from OpenClaw | `hermes claw migrate` |

If anything behaves oddly after an install or an upgrade, `hermes doctor` is the
first thing to reach for — it checks the environment and reports what is missing
or misconfigured rather than making you guess.

---

## What else it does

**Messaging gateways.** Hermes can be driven from Telegram, Discord, Slack,
WhatsApp, Signal, or the CLI. `hermes gateway` wires these up. This is what makes
a small always-on VPS worth considering: the agent stays reachable from your
phone without your laptop needing to be awake.

**Scheduling.** There is a built-in cron scheduler for unattended runs, so
recurring jobs do not need an external trigger.

**Parallel execution.** It can spawn isolated subagents to run concurrent
workstreams rather than serialising everything through one conversation.

**Terminal interface.** A full TUI with multiline editing and command
autocomplete, if you prefer to stay in the terminal.

---

## How this relates to this repo

Hermes Agent is a general-purpose agent, not a trading system, and it does not
replace or overlap with anything in this repository. The two are independent.

It is worth being deliberate about one specific temptation, though. Hermes has
shell access, and this repo exposes a CLI for placing trades, so it is
technically straightforward to let an autonomous agent drive the trading engine.
Everything in this project is deliberately scoped to **paper trading** on a
simulated account, and that boundary is doing real work — it means a bad
decision costs nothing. Wiring a self-directing agent into a live-money broker
account removes that safety net entirely, and no amount of prompt-level
instruction substitutes for it. If you ever explore that direction, keep it on
paper, and keep the risk controls described in `docs/TRADING_PLAN.md` in the
execution path rather than in the agent's instructions.

---

## Sources

- Repository and README: <https://github.com/NousResearch/hermes-agent> (MIT licence)
- Installation guide: <https://hermes-agent.nousresearch.com/docs/getting-started/installation>
- Documentation home: <https://hermes-agent.nousresearch.com/docs/>
- Community: <https://discord.gg/NousResearch> · Skills hub: <https://agentskills.io>

Note that the `hermes-agent.nousresearch.com` links above resolve normally from
your own machine. They are only unreachable from inside a Claude Code web
session, for the egress reason described at the top of this document.

Install commands, the command reference, the feature list and the licence were
taken from the project's official GitHub README. The prerequisite list and the
`hermes setup --portal` flow come from the project's published installation and
quickstart documentation.
