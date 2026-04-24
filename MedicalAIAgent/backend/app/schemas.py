from pydantic import BaseModel, Field
from typing import List

class Hospital(BaseModel):
    name: str
    address: str
    lat: float
    lon: float

class CaseResponse(BaseModel):
    case_id: str
    timestamp: str
    case_summary: str
    safe_insights: List[str] = Field(default_factory=list)
    hospital_results: List[Hospital] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    disclaimer: str
    stored_csv_path: str
    memory_summary: str
