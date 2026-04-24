from pydantic import BaseModel, Field
from typing import Dict, List, Literal


class Hospital(BaseModel):
    name: str
    address: str
    lat: float
    lon: float


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str


class CaseResponse(BaseModel):
    case_id: str
    timestamp: str
    case_summary: str
    mri_interpretation: List[str] = Field(default_factory=list)
    safe_insights: List[str] = Field(default_factory=list)
    hospital_results: List[Hospital] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    tool_decisions: Dict[str, bool] = Field(default_factory=dict)
    disclaimer: str
    stored_csv_path: str
    memory_summary: str
    chat_history: List[ChatMessage] = Field(default_factory=list)


class SessionHistoryResponse(BaseModel):
    session_id: str
    memory_summary: str
    chat_history: List[ChatMessage] = Field(default_factory=list)


class ClearSessionResponse(BaseModel):
    session_id: str
    cleared: bool
