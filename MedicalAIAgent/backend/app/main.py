from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional
from .agent import MedicalAgent
from .schemas import CaseResponse, ClearSessionResponse, SessionHistoryResponse

app = FastAPI(title="Medical AI Assistant Agent", version="1.0.0")
CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "cases.csv"
agent = MedicalAgent(csv_path=str(CSV_PATH))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/session-history/{session_id}", response_model=SessionHistoryResponse)
def session_history(session_id: str):
    return agent.get_session_history(session_id)


@app.delete("/api/session/{session_id}", response_model=ClearSessionResponse)
def clear_session(session_id: str):
    return ClearSessionResponse(session_id=session_id, cleared=agent.clear_session(session_id))


@app.post("/api/analyze-case", response_model=CaseResponse)
async def analyze_case(
    text_input: str = Form(...),
    mri_description: Optional[str] = Form(None),
    session_id: str = Form("default-session"),
    mri_image: Optional[UploadFile] = File(None),
):
    cleaned_mri_description = (mri_description or "").strip()
    if mri_image and not cleaned_mri_description:
        raise HTTPException(
            status_code=422,
            detail="MRI/scan description is required when an image is provided.",
        )

    image_info = None
    if mri_image:
        content = await mri_image.read()
        image_info = (mri_image.filename or "uploaded_file", len(content))
    return await agent.analyze(session_id, text_input, cleaned_mri_description or None, image_info)
