from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class SessionMemory:
    summary: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)


class ConversationMemory:
    def __init__(
        self,
        max_chars: int = 4000,
        trim_target_ratio: float = 0.65,
        summary_max_chars: int = 1200,
    ):
        self.max_chars = max_chars
        self.trim_target_ratio = trim_target_ratio
        self.summary_max_chars = summary_max_chars
        self.sessions: Dict[str, SessionMemory] = defaultdict(SessionMemory)

    def add_message(self, session_id: str, role: str, content: str, timestamp: str | None = None) -> str:
        session = self.sessions[session_id]
        session.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            }
        )
        self._trim_and_summarize(session)
        return session.summary

    def clear_session(self, session_id: str) -> bool:
        existed = session_id in self.sessions
        if existed:
            del self.sessions[session_id]
        return existed

    def _message_cost(self, msg: Dict[str, str]) -> int:
        return len(msg["role"]) + len(msg["content"]) + len(msg["timestamp"])

    def _session_cost(self, session: SessionMemory) -> int:
        return len(session.summary) + sum(self._message_cost(msg) for msg in session.messages)

    def _compress_removed_messages(self, removed: List[Dict[str, str]]) -> str:
        chunks = []
        for msg in removed:
            role = msg["role"]
            content = " ".join(msg["content"].strip().split())
            if len(content) > 180:
                content = content[:177].rstrip() + "..."
            chunks.append(f"{role}: {content}")
        return " | ".join(chunks)

    def _trim_and_summarize(self, session: SessionMemory):
        total = self._session_cost(session)
        if total <= self.max_chars:
            return

        removed: List[Dict[str, str]] = []
        target = int(self.max_chars * self.trim_target_ratio)
        while session.messages and total > target:
            removed.append(session.messages.pop(0))
            total = self._session_cost(session)

        if not removed:
            return

        compressed = self._compress_removed_messages(removed)
        if session.summary:
            session.summary = f"{session.summary} || {compressed}"
        else:
            session.summary = compressed
        session.summary = session.summary[: self.summary_max_chars]

    def get_summary(self, session_id: str) -> str:
        return self.sessions[session_id].summary

    def get_history(self, session_id: str, limit: int | None = None) -> List[Dict[str, str]]:
        history = self.sessions[session_id].messages
        if limit is None:
            return list(history)
        return list(history[-limit:])

    def get_context_text(self, session_id: str, recent_limit: int = 6) -> str:
        session = self.sessions[session_id]
        recent = self.get_history(session_id, limit=recent_limit)
        recent_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
        if session.summary and recent_text:
            return f"Summary of earlier context: {session.summary}\nRecent context:\n{recent_text}"
        if session.summary:
            return f"Summary of earlier context: {session.summary}"
        return recent_text
