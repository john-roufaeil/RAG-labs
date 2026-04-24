from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List

@dataclass
class SessionMemory:
    summary: str = ""
    messages: List[str] = field(default_factory=list)

class ConversationMemory:
    def __init__(self, max_chars: int = 4000):
        self.max_chars = max_chars
        self.sessions: Dict[str, SessionMemory] = defaultdict(SessionMemory)

    def add_message(self, session_id: str, role: str, content: str) -> str:
        session = self.sessions[session_id]
        session.messages.append(f"{role}: {content}")
        self._trim_and_summarize(session)
        return session.summary

    def _trim_and_summarize(self, session: SessionMemory):
        total = len(session.summary) + sum(len(m) for m in session.messages)
        if total <= self.max_chars:
            return
        removed = []
        while session.messages and total > self.max_chars * 0.65:
            msg = session.messages.pop(0)
            removed.append(msg)
            total = len(session.summary) + sum(len(m) for m in session.messages)
        if removed:
            compact = " | ".join(removed)
            compact = compact[:700]
            if session.summary:
                session.summary = (session.summary + " || " + compact)[:1200]
            else:
                session.summary = compact[:1200]

    def get_summary(self, session_id: str) -> str:
        return self.sessions[session_id].summary
