from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

try:
    from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, ToolMessage
    from langchain_core.tools import tool
except Exception:
    from langchain.messages import AIMessage, HumanMessage, RemoveMessage, ToolMessage
    from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field
from tavily import TavilyClient

from .memory import ConversationMemory
from .schemas import CaseResponse, ChatMessage, Hospital, SessionHistoryResponse
from .tools import CaseCSVStore, as_json_string, flatten_message_content, load_project_env, try_load_json

load_project_env()

try:
    from langchain.agents import AgentState, create_agent as modern_create_agent
    from langchain.agents.middleware import SummarizationMiddleware, before_agent
    HAS_MODERN_AGENT = True
except Exception:
    from langgraph.prebuilt import create_react_agent
    AgentState = Dict[str, Any]  # type: ignore
    HAS_MODERN_AGENT = False

    def before_agent(func):
        return func


DISCLAIMER = 'This is not a medical diagnosis. Consult a doctor.'


class MedicalStructuredResponse(BaseModel):
    case_summary: str = Field(default='')
    mri_interpretation: List[str] = Field(default_factory=list)
    safe_insights: List[str] = Field(default_factory=list)
    disclaimers: List[str] = Field(default_factory=list)


@before_agent
def trim_messages(state: AgentState, runtime: Any) -> dict[str, Any] | None:
    messages = state['messages']
    tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
    if not tool_messages:
        return None
    return {'messages': [RemoveMessage(id=message.id) for message in tool_messages]}


class MedicalAgent:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.memory = ConversationMemory(max_chars=4200)
        self.csv_store = CaseCSVStore(csv_path)
        self.thread_versions: Dict[str, int] = {}
        self.model_name = os.getenv('MEDICAL_AGENT_MODEL', 'gpt-4.1')
        self.tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY')) if os.getenv('TAVILY_API_KEY') else None
        self.graph_agent = self._build_agent()

    def _build_agent(self):
        csv_store = self.csv_store
        tavily_client = self.tavily_client

        @tool('WebSearch')
        def web_search(diagnoses: str, location: str) -> str:
            """Search nearby hospitals for a diagnosis and location."""
            if not tavily_client:
                return as_json_string({'results': [], 'error': 'TAVILY_API_KEY missing'})
            query = f'nearest hospital for {diagnoses} near {location}'
            try:
                response = tavily_client.search(query)
                return as_json_string(response)
            except Exception as exc:
                return as_json_string({'results': [], 'error': str(exc)})

        @tool('CSVStorageTool')
        def csv_storage_tool(case_payload: str) -> str:
            """Store structured case payload JSON into CSV and return success state."""
            payload = try_load_json(case_payload)
            if not payload:
                return as_json_string({'stored': False, 'reason': 'invalid payload'})
            csv_store.save(payload)
            return as_json_string({'stored': True, 'path': csv_store.csv_path})

        system_prompt = (
            'You are a Medical AI Assistant Agent. '
            'Never provide diagnosis or prescriptions. '
            'Always include this exact disclaimer: This is not a medical diagnosis. Consult a doctor. '
            'Provide safe, conservative support. '
            'If the user asks for nearby hospitals, use WebSearch. '
            'Store structured case payloads with CSVStorageTool. '
            'Respond with concise fields for case_summary, mri_interpretation, safe_insights, disclaimers.'
        )

        if HAS_MODERN_AGENT:
            return modern_create_agent(
                model=self.model_name,
                system_prompt=system_prompt,
                tools=[web_search, csv_storage_tool],
                checkpointer=InMemorySaver(),
                middleware=[
                    SummarizationMiddleware(
                        model='gpt-4o-mini',
                        trigger=('tokens', 100),
                        keep=('messages', 1),
                    ),
                    trim_messages,
                ],
                response_format=MedicalStructuredResponse,
            )

        return create_react_agent(
            model=self.model_name,
            tools=[web_search, csv_storage_tool],
            checkpointer=InMemorySaver(),
            state_modifier=system_prompt,
            response_format=MedicalStructuredResponse,
        )

    def _thread_id(self, session_id: str) -> str:
        version = self.thread_versions.get(session_id, 0)
        return f'{session_id}:{version}'

    def _extract_tool_usage(self, messages: List[Any]) -> Dict[str, bool]:
        used = {'search_tool': False, 'csv_storage_tool': False}
        for message in messages:
            if isinstance(message, AIMessage):
                for call in getattr(message, 'tool_calls', []) or []:
                    tool_name = str(call.get('name', '')).lower()
                    if tool_name == 'websearch':
                        used['search_tool'] = True
                    if tool_name == 'csvstoragetool':
                        used['csv_storage_tool'] = True
        return used

    def _extract_hospitals(self, messages: List[Any]) -> List[Hospital]:
        hospitals: List[Hospital] = []
        for message in messages:
            if not isinstance(message, ToolMessage):
                continue
            tool_name = str(getattr(message, 'name', '') or '').lower()
            if tool_name != 'websearch':
                continue
            parsed = try_load_json(flatten_message_content(message.content))
            for item in parsed.get('results', [])[:5]:
                title = str(item.get('title') or item.get('name') or 'Hospital')
                address = str(item.get('content') or item.get('url') or 'Address unavailable')
                hospitals.append(Hospital(name=title, address=address, lat=0.0, lon=0.0))
        return hospitals[:5]

    def _assistant_text(self, result: Dict[str, Any]) -> str:
        structured = result.get('structured_response')
        if structured:
            lines = [f"Case summary: {structured.case_summary}", 'MRI interpretation:']
            for item in structured.mri_interpretation:
                lines.append(f'- {item}')
            lines.append('Safe insights:')
            for item in structured.safe_insights:
                lines.append(f'- {item}')
            lines.append(DISCLAIMER)
            return '\n'.join(lines)

        messages = result.get('messages', [])
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                text = flatten_message_content(message.content)
                if text.strip():
                    return text
        return DISCLAIMER

    async def analyze(
        self,
        session_id: str,
        text_input: str,
        mri_description: Optional[str],
        image_info: Optional[Tuple[str, int, Optional[str], Optional[str]]],
    ) -> CaseResponse:
        now = datetime.now(timezone.utc).isoformat()
        case_id = f'CASE-{uuid4().hex[:10].upper()}'

        image_name = ''
        image_size = 0
        image_b64 = None
        image_mime = 'image/png'
        if image_info:
            image_name, image_size, image_b64, image_mime = image_info

        merged = text_input + (' ' + mri_description if mri_description else '')
        self.memory.add_message(session_id, 'user', merged, now)

        content_blocks: List[Dict[str, Any]] = [
            {
                'type': 'text',
                'text': (
                    f'Symptoms: {text_input}\n'
                    f'MRI description: {mri_description or "(none)"}\n'
                    f'Image file: {image_name or "(none)"}\n'
                    'Provide safe insights and use tools when needed.'
                ),
            }
        ]
        if image_b64:
            content_blocks.append({'type': 'image', 'base64': image_b64, 'mime_type': image_mime or 'image/png'})

        invoke_result = self.graph_agent.invoke(
            {'messages': [HumanMessage(content=content_blocks)]},
            {'configurable': {'thread_id': self._thread_id(session_id)}},
        )

        structured = invoke_result.get('structured_response')
        messages = invoke_result.get('messages', [])
        tool_decisions = self._extract_tool_usage(messages)

        mri_interpretation = list(getattr(structured, 'mri_interpretation', []) or [])
        safe_insights = list(getattr(structured, 'safe_insights', []) or [])
        case_summary = str(getattr(structured, 'case_summary', '') or '').strip()

        if not case_summary:
            case_summary = f'Primary symptoms: {text_input.strip()}'
        if not mri_interpretation:
            mri_interpretation = ['MRI description reviewed. Please correlate with formal radiology interpretation.']
        if not safe_insights:
            safe_insights = ['Monitor symptoms and seek urgent in-person care for worsening neurological signs.']

        hospitals = self._extract_hospitals(messages)
        tools_used = [
            'websearch' if tool_decisions['search_tool'] else None,
            'csvstoragetool' if tool_decisions['csv_storage_tool'] else None,
        ]
        tools_used = [tool_name for tool_name in tools_used if tool_name]

        assistant_message = self._assistant_text(invoke_result)
        self.memory.add_message(session_id, 'assistant', assistant_message)

        if not tool_decisions['csv_storage_tool']:
            self.csv_store.save(
                {
                    'timestamp': now,
                    'case_id': case_id,
                    'session_id': session_id,
                    'text_input': text_input,
                    'mri_description': mri_description or '',
                    'image_name': image_name,
                    'image_size_bytes': image_size,
                    'case_summary': case_summary,
                    'mri_interpretation': mri_interpretation,
                    'safe_insights': safe_insights,
                    'hospitals_count': len(hospitals),
                    'tools_used': tools_used,
                    'tool_decisions': tool_decisions,
                    'disclaimer': DISCLAIMER,
                }
            )

        return CaseResponse(
            case_id=case_id,
            timestamp=now,
            case_summary=case_summary,
            mri_interpretation=mri_interpretation,
            safe_insights=safe_insights,
            hospital_results=hospitals,
            tools_used=tools_used,
            tool_decisions=tool_decisions,
            disclaimer=DISCLAIMER,
            stored_csv_path=self.csv_path,
            memory_summary=self.memory.get_summary(session_id) or 'Summarization middleware active when supported by LangChain version.',
            chat_history=[ChatMessage(**msg) for msg in self.memory.get_history(session_id, limit=40)],
        )

    def get_session_history(self, session_id: str) -> SessionHistoryResponse:
        return SessionHistoryResponse(
            session_id=session_id,
            memory_summary=self.memory.get_summary(session_id) or 'Summarization middleware active when supported by LangChain version.',
            chat_history=[ChatMessage(**msg) for msg in self.memory.get_history(session_id, limit=40)],
        )

    def clear_session(self, session_id: str) -> bool:
        self.thread_versions[session_id] = self.thread_versions.get(session_id, 0) + 1
        return self.memory.clear_session(session_id)
