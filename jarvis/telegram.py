"""
Minimal Telegram Bot API client (long polling, no framework dependency).
"""
import requests

TELEGRAM_LIMIT = 4000  # Telegram caps messages at 4096 characters


def chunk_text(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    """Split long replies at line or word boundaries so nothing is cut mid-sentence."""
    text = (text or "").strip()
    if not text:
        return ["(empty reply)"]
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = text.rfind(" ", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    chunks.append(text)
    return chunks


class TelegramBot:
    def __init__(self, token: str):
        self.base = f"https://api.telegram.org/bot{token}"
        self.file_base = f"https://api.telegram.org/file/bot{token}"

    def _post(self, method: str, timeout: int = 30, **kwargs) -> dict:
        try:
            r = requests.post(f"{self.base}/{method}", timeout=timeout, **kwargs)
            data = r.json()
        except Exception as e:  # noqa: BLE001
            print(f"[telegram] {method} error: {e}")
            return {}
        if not data.get("ok"):
            print(f"[telegram] {method} failed: {str(data)[:200]}")
        return data

    def get_me(self) -> dict:
        return self._post("getMe").get("result", {}) or {}

    def get_updates(self, offset: int | None, timeout: int = 30) -> list:
        payload = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset
        data = self._post("getUpdates", timeout=timeout + 15, json=payload)
        return data.get("result", []) or []

    def send_message(self, chat_id, text: str) -> None:
        for chunk in chunk_text(text):
            self._post("sendMessage", json={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            })

    def send_action(self, chat_id, action: str = "typing") -> None:
        self._post("sendChatAction", json={"chat_id": chat_id, "action": action})

    def send_audio(self, chat_id, audio: bytes, title: str = "Jarvis") -> None:
        self._post(
            "sendAudio", timeout=90,
            data={"chat_id": str(chat_id), "title": title, "performer": title},
            files={"audio": (f"{title.lower()}.mp3", audio, "audio/mpeg")},
        )

    def download(self, file_id: str) -> bytes | None:
        info = self._post("getFile", json={"file_id": file_id})
        path = (info.get("result") or {}).get("file_path")
        if not path:
            return None
        try:
            r = requests.get(f"{self.file_base}/{path}", timeout=60)
            return r.content if r.ok else None
        except Exception as e:  # noqa: BLE001
            print(f"[telegram] download error: {e}")
            return None
