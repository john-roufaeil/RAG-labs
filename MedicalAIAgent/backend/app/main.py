from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from .agent import MedicalAgent
from .schemas import CaseResponse

app = FastAPI(title="Medical AI Assistant Agent", version="1.0.0")
agent = MedicalAgent(csv_path="backend/data/cases.csv")

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

@app.post("/api/analyze-case", response_model=CaseResponse)
async def analyze_case(
    text_input: str = Form(...),
    mri_description: Optional[str] = Form(None),
    session_id: str = Form("default-session"),
    mri_image: Optional[UploadFile] = File(None),
):
    image_info = None
    if mri_image:
        content = await mri_image.read()
        image_info = (mri_image.filename or "uploaded_file", len(content))
    return await agent.analyze(session_id, text_input, mri_description, image_info)
