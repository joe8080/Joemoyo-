"""
Jarvis runner: the always-on Telegram loop.

Reads updates by long polling, answers only the authorised chat, transcribes
voice notes, runs the brain, persists the conversation to the Vault, and
replies by text (and by voice when ElevenLabs is configured).
"""
import sys
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

from . import voice
from .brain import Jarvis, _gbp, _pct
from .config import JarvisConfig, load_config
from .content import OGX
from .telegram import TelegramBot
from .vault import Vault

LONDON = ZoneInfo("Europe/London")

HELP = """I'm {name}. Talk to me by voice note or text.

Commands:
/brief  morning brief: portfolio, goals, decisions, content
/portfolio  live portfolio summary and top holdings
/goals  active goals
/rules  the binding agent rules
/new  start a fresh conversation
/close  summarise this session and save it to the Vault
/refresh  reload the live context from the databases
/voice on  or  /voice off  spoken replies
/help  this list

Anything else, just ask. I log decisions, ideas and memories as we go."""

BRIEF_PROMPT = (
    "Give me my morning brief. Pull the live portfolio summary, the top holdings, active goals, "
    "the last five decisions, the content pipeline, any open content flags and the latest competitive "
    "headline. Numbered, voice-friendly, under 250 words, and finish with the single most important "
    "action for today."
)

CLOSE_PROMPT = (
    "We are closing this session. Summarise what we covered, the decisions made and the action items, "
    "then save it with log_session_capture using the main topic as the domain. Reply with the summary "
    "in under 120 words."
)


class JarvisRunner:
    def __init__(self, cfg: JarvisConfig, vault=None, ogx=None, brain=None, bot=None):
        self.cfg = cfg
        self.vault = vault or Vault(cfg.vault_url, cfg.vault_key)
        self.ogx = ogx or OGX(cfg.ogx_url, cfg.ogx_key)
        self.brain = brain or Jarvis(cfg, self.vault, self.ogx)
        self.bot = bot or TelegramBot(cfg.telegram_token)
        self.allowed_chat = cfg.telegram_chat_id or (self.vault.telegram_chat_id() if self.vault.enabled else "")
        self.voice_replies = cfg.voice_replies
        self.history: list = []
        self.conversation_id = None
        self.offset: int | None = None

    # ---- conversation state ----------------------------------------------- #

    def start_conversation(self, title: str | None = None):
        title = title or f"Telegram {datetime.now(LONDON):%Y-%m-%d %H:%M}"
        self.history = []
        self.conversation_id = self.vault.start_conversation(self.brain.owner_key, title) if self.vault.enabled else None
        self.brain.conversation_id = self.conversation_id
        return self.conversation_id

    def resume_or_start(self):
        """Continue today's Telegram conversation if one exists, else start a new one."""
        if self.vault.enabled:
            today = f"Telegram {datetime.now(LONDON):%Y-%m-%d}"
            existing = self.vault.latest_conversation(self.brain.owner_key, today)
            if existing.get("id"):
                self.conversation_id = existing["id"]
                self.brain.conversation_id = self.conversation_id
                rows = self.vault.conversation_messages(self.conversation_id, limit=self.cfg.history_turns * 2)
                self.history = [
                    {"role": r["role"], "content": r["content"]}
                    for r in rows if r.get("role") in ("user", "assistant") and r.get("content")
                ]
                self._trim_history()
                return self.conversation_id
        return self.start_conversation()

    def _trim_history(self):
        keep = self.cfg.history_turns * 2
        if len(self.history) > keep:
            self.history = self.history[-keep:]
        # history must start with a user turn
        while self.history and self.history[0]["role"] != "user":
            self.history.pop(0)

    def _remember_turn(self, user_text: str, assistant_text: str):
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": assistant_text})
        self._trim_history()
        self.vault.log_message(self.brain.owner_key, self.conversation_id, "user", user_text)
        self.vault.log_message(self.brain.owner_key, self.conversation_id, "assistant", assistant_text)

    # ---- authorisation ---------------------------------------------------- #

    def authorised(self, chat_id) -> bool:
        return bool(self.allowed_chat) and str(chat_id) == str(self.allowed_chat)

    # ---- handlers --------------------------------------------------------- #

    def handle_command(self, chat_id, text: str) -> bool:
        cmd, _, arg = text.strip().partition(" ")
        cmd = cmd.lower().split("@")[0]
        if cmd in ("/start", "/help"):
            self.bot.send_message(chat_id, HELP.format(name=self.cfg.assistant_name))
        elif cmd == "/new":
            self.start_conversation()
            self.bot.send_message(chat_id, "Fresh conversation started.")
        elif cmd == "/refresh":
            self.brain.refresh_context()
            self.bot.send_message(chat_id, "Live context reloaded from the Vault and the OGX database.")
        elif cmd == "/voice":
            self.voice_replies = arg.strip().lower() not in ("off", "0", "no")
            state = "on" if self.voice_replies else "off"
            if self.voice_replies and not self.cfg.can_speak:
                state = "on, but ElevenLabs is not configured so replies stay as text"
            self.bot.send_message(chat_id, f"Spoken replies {state}.")
        elif cmd == "/portfolio":
            self.bot.send_message(chat_id, self._portfolio_text())
        elif cmd == "/goals":
            self.bot.send_message(chat_id, self._goals_text())
        elif cmd == "/rules":
            self.bot.send_message(chat_id, self._rules_text(arg.strip() or None))
        elif cmd == "/brief":
            self.handle_text(chat_id, BRIEF_PROMPT, spoken=True)
        elif cmd == "/close":
            self.handle_text(chat_id, CLOSE_PROMPT, spoken=False)
            self.start_conversation()
        else:
            return False
        return True

    def handle_text(self, chat_id, text: str, spoken: bool = False):
        self.bot.send_action(chat_id, "typing")
        try:
            answer, tools_used = self.brain.reply(text, self.history)
        except anthropic.RateLimitError:
            self.bot.send_message(chat_id, "Claude is rate limited right now. Give me a minute and try again.")
            return
        except anthropic.AuthenticationError:
            self.bot.send_message(chat_id, "My Anthropic key is invalid. Check ANTHROPIC_API_KEY on the server.")
            return
        except anthropic.APIStatusError as e:
            self.bot.send_message(chat_id, f"Claude returned an error ({e.status_code}). Try again shortly.")
            return
        except anthropic.APIConnectionError:
            self.bot.send_message(chat_id, "I can't reach Claude right now. Network problem on my side.")
            return
        if tools_used:
            print(f"[jarvis] tools: {', '.join(tools_used)}")
        self._remember_turn(text, answer)
        self.bot.send_message(chat_id, answer)
        if spoken and self.voice_replies and self.cfg.can_speak:
            self.bot.send_action(chat_id, "record_voice")
            audio = voice.synthesize(self.cfg, answer)
            if audio:
                self.bot.send_audio(chat_id, audio, title=self.cfg.assistant_name)

    def handle_voice(self, chat_id, file_id: str):
        if not self.cfg.can_transcribe:
            self.bot.send_message(chat_id, "I can't hear voice notes yet. Add OPENAI_API_KEY or ELEVENLABS_API_KEY on the server, or send text.")
            return
        self.bot.send_action(chat_id, "typing")
        audio = self.bot.download(file_id)
        transcript = voice.transcribe(self.cfg, audio) if audio else None
        if not transcript:
            self.bot.send_message(chat_id, "I couldn't make out that voice note. Try again or send text.")
            return
        self.bot.send_message(chat_id, f"Heard: {transcript}")
        if transcript.startswith("/") and self.handle_command(chat_id, transcript):
            return
        self.handle_text(chat_id, transcript, spoken=True)

    def handle_update(self, update: dict):
        msg = update.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        if chat_id is None:
            return
        if not self.authorised(chat_id):
            print(f"[jarvis] ignored message from unauthorised chat {chat_id}")
            self.bot.send_message(chat_id, f"Not authorised. This chat id is {chat_id}. Set it as TELEGRAM_CHAT_ID on the server.")
            return
        if msg.get("voice") or msg.get("audio"):
            file_id = (msg.get("voice") or msg.get("audio") or {}).get("file_id")
            if file_id:
                self.handle_voice(chat_id, file_id)
            return
        text = (msg.get("text") or msg.get("caption") or "").strip()
        if not text:
            self.bot.send_message(chat_id, "Send me text or a voice note.")
            return
        if text.startswith("/") and self.handle_command(chat_id, text):
            return
        self.handle_text(chat_id, text, spoken=bool(self.voice_replies))

    # ---- direct Vault views (no Claude call, instant and free) ------------- #

    def _portfolio_text(self) -> str:
        ps = self.vault.portfolio_summary()
        if not ps:
            return "The Vault has no portfolio summary yet."
        lines = [
            f"Portfolio on {ps.get('snapshot_date')}:",
            f"1. Total {_gbp(ps.get('total_value_gbp'))}. ISA {_gbp(ps.get('isa_value_gbp'))}. Invest {_gbp(ps.get('gia_value_gbp'))}.",
            f"2. Profit {_gbp(ps.get('total_pnl_gbp'))}, which is {_pct(ps.get('total_pnl_pct'))}.",
            f"3. North star progress {_pct(ps.get('progress_pct'))} of one million.",
        ]
        holdings = self.vault.holdings(limit=10)
        if holdings:
            lines.append("Top holdings:")
            for i, h in enumerate(holdings, 1):
                lines.append(
                    f"{i}. {h.get('ticker')} {_gbp(h.get('current_value_gbp'))} "
                    f"({_pct(h.get('pnl_pct'))}) in {h.get('account')}"
                )
        return "\n".join(lines)

    def _goals_text(self) -> str:
        goals = self.vault.goals()
        if not goals:
            return "No active goals in the Vault."
        lines = ["Active goals:"]
        for i, g in enumerate(goals, 1):
            note = (g.get("notes") or "").strip()
            lines.append(f"{i}. {g.get('goal_name')}: {g.get('status')}, {_pct(g.get('progress_pct'))} done. {note}".rstrip())
        return "\n".join(lines)

    def _rules_text(self, domain: str | None = None) -> str:
        rules = self.vault.rules(domain)
        if not rules:
            return "No rules found" + (f" for {domain}." if domain else " in the Vault.")
        lines = [f"{len(rules)} rules" + (f" for {domain}:" if domain else ":")]
        for i, r in enumerate(rules, 1):
            lines.append(f"{i}. {r.get('rule_name')} ({r.get('domain')}): {r.get('rule_text')}")
        return "\n".join(lines)

    # ---- main loop -------------------------------------------------------- #

    def heartbeat(self):
        me = self.bot.get_me()
        stt = "whisper" if self.cfg.openai_api_key else ("scribe" if self.cfg.elevenlabs_api_key else "none")
        print("=" * 60)
        print(f"{self.cfg.assistant_name} online as @{me.get('username', '?')}")
        print(f"  model {self.cfg.model} | effort {self.cfg.effort} | fallbacks {'on' if self.brain.fallbacks_enabled else 'off'}")
        print(f"  vault {'ok' if self.vault.enabled else 'NOT CONFIGURED'} | ogx {'ok' if self.ogx.enabled else 'not configured'}")
        print(f"  allowed chat {'set' if self.allowed_chat else 'NOT SET: message the bot to learn your chat id'}")
        print(f"  voice in {stt} | voice out {'elevenlabs' if self.cfg.can_speak else 'none'}")
        print(f"  conversation {self.conversation_id or 'not persisted'}")
        print("=" * 60, flush=True)

    def run(self):
        self.resume_or_start()
        self.brain.refresh_context()
        self.heartbeat()
        backoff = 2
        while True:
            try:
                updates = self.bot.get_updates(self.offset, timeout=self.cfg.poll_timeout)
                backoff = 2
            except Exception as e:  # noqa: BLE001
                print(f"[jarvis] poll error: {e}; retrying in {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            for update in updates:
                self.offset = int(update.get("update_id", 0)) + 1
                try:
                    self.handle_update(update)
                except Exception as e:  # noqa: BLE001
                    traceback.print_exc()
                    chat_id = ((update.get("message") or {}).get("chat") or {}).get("id")
                    if chat_id is not None and self.authorised(chat_id):
                        self.bot.send_message(chat_id, f"Something broke on my side: {type(e).__name__}. Try again.")


def main():
    cfg = load_config()
    missing = [n for n, v in (("ANTHROPIC_API_KEY", cfg.anthropic_api_key),
                              ("TELEGRAM_BOT_TOKEN", cfg.telegram_token)) if not v]
    if missing:
        print(f"Jarvis cannot start. Missing: {', '.join(missing)}")
        sys.exit(1)
    if not cfg.vault_enabled:
        print("Warning: SUPABASE_URL / SUPABASE_SERVICE_KEY not set. Jarvis will run without the Vault.")
    JarvisRunner(cfg).run()


if __name__ == "__main__":
    main()
