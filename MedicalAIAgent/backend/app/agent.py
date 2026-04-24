from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, List, Optional, Tuple
from .memory import ConversationMemory
from .tools import (
    CSVStorageTool,
    HospitalSearchTool,
    MRIInterpretationTool,
    extract_location,
    should_use_csv_storage_tool,
    should_use_search_tool,
)
from .schemas import CaseResponse, ChatMessage, Hospital, SessionHistoryResponse

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
        self.csv_path = csv_path
        self.csv_tool = CSVStorageTool(csv_path)
        self.mri_tool = MRIInterpretationTool()

    def _safe_insights(self, combined_text: str, context_text: str = "") -> List[str]:
        text = f"{context_text} {combined_text}".lower()
        insights = []
        for key, value in KEYWORD_INSIGHTS.items():
            if key in text:
                insights.append(value)
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

    def _build_assistant_message(
        self,
        case_summary: str,
        mri_interpretation: List[str],
        safe_insights: List[str],
        hospitals: List[Hospital],
    ) -> str:
        lines = [f"Case summary: {case_summary}", "MRI interpretation:"]
        for item in mri_interpretation:
            lines.append(f"- {item}")
        lines.append("Safe insights:")
        for insight in safe_insights:
            lines.append(f"- {insight}")
        if hospitals:
            lines.append("Nearby hospitals:")
            for hospital in hospitals[:5]:
                lines.append(f"- {hospital.name} — {hospital.address}")
        lines.append(DISCLAIMER)
        return "\n".join(lines)

    def _chat_history(self, session_id: str, limit: int = 40) -> List[ChatMessage]:
        history = self.memory.get_history(session_id, limit=limit)
        return [ChatMessage(**msg) for msg in history]

    def clear_session(self, session_id: str) -> bool:
        return self.memory.clear_session(session_id)

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
        self.memory.add_message(session_id, "user", merged, now)

        search_decision = should_use_search_tool(text_input)
        csv_decision = should_use_csv_storage_tool(text_input, mri_description, image_info)
        tool_decisions: Dict[str, bool] = {
            "search_tool": search_decision,
            "csv_storage_tool": csv_decision,
            "mri_interpretation_tool": True,
        }

        tools_used = ["mri_interpretation_tool"]
        hospitals: List[Hospital] = []
        if search_decision:
            location = extract_location(text_input)
            raw = self.search_tool.search(location, limit=5)
            hospitals = [Hospital(**hospital) for hospital in raw]
            tools_used.append("search_tool")

        summary = self._build_summary(text_input, mri_description, image_name, image_size)
        mri_interpretation = self.mri_tool.interpret(mri_description, image_info)
        context_text = self.memory.get_context_text(session_id, recent_limit=6)
        safe_insights = self._safe_insights(merged, context_text=context_text)
        assistant_message = self._build_assistant_message(summary, mri_interpretation, safe_insights, hospitals)
        self.memory.add_message(session_id, "assistant", assistant_message)

        if csv_decision:
            tools_used.append("csv_storage_tool")
            self.csv_tool.save(
                {
                    "timestamp": now,
                    "case_id": case_id,
                    "session_id": session_id,
                    "text_input": text_input,
                    "mri_description": mri_description or "",
                    "image_name": image_name,
                    "image_size_bytes": image_size,
                    "case_summary": summary,
                    "mri_interpretation": mri_interpretation,
                    "safe_insights": safe_insights,
                    "hospitals_count": len(hospitals),
                    "tools_used": tools_used,
                    "disclaimer": DISCLAIMER,
                }
            )

        return CaseResponse(
            case_id=case_id,
            timestamp=now,
            case_summary=summary,
            mri_interpretation=mri_interpretation,
            safe_insights=safe_insights,
            hospital_results=hospitals,
            tools_used=tools_used,
            tool_decisions=tool_decisions,
            disclaimer=DISCLAIMER,
            stored_csv_path=self.csv_path if csv_decision else "",
            memory_summary=self.memory.get_summary(session_id),
            chat_history=self._chat_history(session_id),
        )

    def get_session_history(self, session_id: str) -> SessionHistoryResponse:
        return SessionHistoryResponse(
            session_id=session_id,
            memory_summary=self.memory.get_summary(session_id),
            chat_history=self._chat_history(session_id),
        )
