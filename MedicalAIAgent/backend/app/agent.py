from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Tuple, List
from .memory import ConversationMemory
from .tools import HospitalSearchTool, CSVStorageTool, should_use_search_tool, extract_location
from .schemas import CaseResponse, Hospital

DISCLAIMER = "This is not a medical diagnosis. Consult a doctor."

KEYWORD_INSIGHTS = {
    "headache": "Persistent headache is a red-flag symptom if worsening, severe, or paired with confusion.",
    "seizure": "Reported seizure activity should be escalated to urgent in-person care.",
    "weakness": "Unilateral weakness requires urgent neurological evaluation.",
    "vision": "New visual disturbance should be assessed promptly by specialists.",
    "nausea": "Severe nausea with neurological symptoms can indicate increased intracranial pressure.",
    "vomit": "Repeated vomiting with neuro symptoms merits urgent medical review.",
    "fever": "Fever with neurological signs may indicate infection and needs immediate care.",
}

class MedicalAgent:
    def __init__(self, csv_path: str):
        self.memory = ConversationMemory(max_chars=4200)
        self.search_tool = HospitalSearchTool()
        self.csv_tool = CSVStorageTool(csv_path)

    def _safe_insights(self, combined_text: str) -> List[str]:
        text = combined_text.lower()
        insights = []
        for k, v in KEYWORD_INSIGHTS.items():
            if k in text:
                insights.append(v)
        if not insights:
            insights.append("Symptoms should be clinically correlated with exam findings and formal radiology review.")
        insights.append("Track symptom onset, progression, and any neurological changes for your clinician.")
        return insights[:5]

    def _build_summary(self, text_input: str, mri_description: Optional[str], image_name: Optional[str], image_size: int) -> str:
        chunks = [f"Primary symptoms: {text_input.strip()}"]
        if mri_description:
            chunks.append(f"MRI description: {mri_description.strip()}")
        if image_name:
            chunks.append(f"Uploaded scan file: {image_name} ({image_size} bytes)")
        return " | ".join(chunks)

    async def analyze(
        self,
        session_id: str,
        text_input: str,
        mri_description: Optional[str],
        image_info: Optional[Tuple[str, int]],
    ) -> CaseResponse:
        now = datetime.now(timezone.utc).isoformat()
        case_id = f"CASE-{uuid4().hex[:10].upper()}"
        image_name, image_size = image_info if image_info else ("", 0)

        merged = text_input + (" " + mri_description if mri_description else "")
        self.memory.add_message(session_id, "user", merged)

        tools_used = ["csv_storage_tool"]
        hospitals = []
        if should_use_search_tool(text_input):
            location = extract_location(text_input)
            raw = self.search_tool.search(location, limit=5)
            hospitals = [Hospital(**h) for h in raw]
            tools_used.append("search_tool")

        summary = self._build_summary(text_input, mri_description, image_name, image_size)
        safe_insights = self._safe_insights(merged)

        response = CaseResponse(
            case_id=case_id,
            timestamp=now,
            case_summary=summary,
            safe_insights=safe_insights,
            hospital_results=hospitals,
            tools_used=tools_used,
            disclaimer=DISCLAIMER,
            stored_csv_path="backend/data/cases.csv",
            memory_summary=self.memory.get_summary(session_id),
        )

        self.memory.add_message(session_id, "assistant", response.case_summary)
        self.csv_tool.save({
            "timestamp": now,
            "case_id": case_id,
            "session_id": session_id,
            "text_input": text_input,
            "mri_description": mri_description or "",
            "image_name": image_name,
            "image_size_bytes": image_size,
            "case_summary": summary,
            "safe_insights": safe_insights,
            "hospitals_count": len(hospitals),
            "tools_used": tools_used,
            "disclaimer": DISCLAIMER,
        })
        return response
