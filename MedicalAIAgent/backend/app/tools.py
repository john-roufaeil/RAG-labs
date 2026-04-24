import csv
import json
import os
import re
from pathlib import Path
import requests
from typing import Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def _load_env_from_project() -> None:
    current = Path(__file__).resolve()
    project_root = current.parents[2]
    env_file = project_root / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_from_project()


def should_use_search_tool(text: str) -> bool:
    normalized = text.lower()
    return any(keyword in normalized for keyword in ["hospital", "nearby", "nearest", "clinic", "emergency"])


def should_use_csv_storage_tool(text: str, mri_description: Optional[str], image_info: Optional[Tuple[str, int]]) -> bool:
    if text.strip():
        return True
    if mri_description and mri_description.strip():
        return True
    if image_info and image_info[0]:
        return True
    return False


def extract_location(text: str) -> str:
    lower = text.lower()
    marker = " in "
    if marker in lower:
        idx = lower.rfind(marker)
        return text[idx + len(marker):].strip(" .,!?")
    return "Beirut"


class HospitalSearchTool:
    def __init__(self):
        self.base = "https://nominatim.openstreetmap.org/search"
        self.headers = {"User-Agent": "medical-ai-agent/1.0"}

    def search(self, location: str, limit: int = 5) -> List[Dict]:
        query = f"hospital in {location}"
        params = {"q": query, "format": "jsonv2", "limit": str(limit)}
        try:
            response = requests.get(self.base, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            out = []
            for item in data:
                out.append(
                    {
                        "name": item.get("name") or item.get("display_name", "Hospital").split(",")[0],
                        "address": item.get("display_name", "Address unavailable"),
                        "lat": float(item["lat"]),
                        "lon": float(item["lon"]),
                    }
                )
            return out
        except Exception:
            return []


class MRIInterpretationTool:
    def __init__(self):
        self.patterns = [
            (r"\blesion\b|\bmass\b|\btumou?r\b", "Focal lesion pattern is mentioned and needs specialist radiology-neurology correlation."),
            (r"\bedema\b|\bswelling\b", "Edema-related wording appears and may reflect inflammatory or pressure-related changes."),
            (r"\bhemorrhage\b|\bbleed\b|\bhematoma\b", "Possible bleeding-related terms are present and require urgent in-person evaluation."),
            (r"\bmidline shift\b", "Midline shift wording is significant and should be escalated urgently."),
            (r"\binfarct\b|\bischemi\w*\b|\bstroke\b", "Ischemic/infarct wording appears and needs urgent stroke-pathway assessment."),
            (r"\bcontrast enhancement\b|\benhancement\b", "Contrast enhancement is reported and should be interpreted with full MRI protocol context."),
            (r"\bt2\b|\bflair\b", "Sequence-specific findings were reported; interpretation should align with full radiology report."),
            (r"\bnormal\b|\bunremarkable\b", "The description suggests no major abnormality wording, but symptoms still need clinical correlation."),
        ]
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

    def _fallback_interpretation(self, mri_description: Optional[str], image_info: Optional[Tuple[str, int]]) -> List[str]:
        output: List[str] = []
        text = (mri_description or "").strip()

        if text:
            found = []
            lowered = text.lower()
            for pattern, message in self.patterns:
                if re.search(pattern, lowered):
                    found.append(message)
            if found:
                output.extend(found[:4])
            else:
                output.append("MRI description received; no specific keyword match was found, so formal radiology review is required.")
        elif image_info:
            file_name, file_size = image_info
            output.append(f"MRI image file '{file_name}' ({file_size} bytes) was uploaded.")
            output.append("Image-only uploads need a formal radiology description for reliable text interpretation in this assistant.")
        else:
            output.append("No MRI description or scan image was provided.")

        output.append("This assistant provides supportive interpretation only and cannot issue a diagnosis.")
        return output

    def _openai_interpretation(self, mri_description: str) -> List[str]:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a medical support assistant. Do not diagnose or prescribe. "
                        "Return JSON with key 'points' containing 3-5 concise, safety-oriented interpretation bullets "
                        "for MRI description text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Interpret this MRI description safely and conservatively. "
                        "Description: " + mri_description
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        points = parsed.get("points", [])
        clean_points = [str(point).strip() for point in points if str(point).strip()]
        return clean_points[:5]

    def interpret(self, mri_description: Optional[str], image_info: Optional[Tuple[str, int]]) -> List[str]:
        text = (mri_description or "").strip()

        if text and self.openai_api_key:
            try:
                result = self._openai_interpretation(text)
                if result:
                    result.append("This assistant provides supportive interpretation only and cannot issue a diagnosis.")
                    return result
            except Exception:
                pass

        return self._fallback_interpretation(mri_description, image_info)


class CSVStorageTool:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as file_obj:
                writer = csv.writer(file_obj)
                writer.writerow(
                    [
                        "timestamp",
                        "case_id",
                        "session_id",
                        "text_input",
                        "mri_description",
                        "image_name",
                        "image_size_bytes",
                        "case_summary",
                        "mri_interpretation",
                        "safe_insights",
                        "hospitals_count",
                        "tools_used",
                        "disclaimer",
                    ]
                )

    def save(self, row: Dict):
        with open(self.csv_path, "a", newline="", encoding="utf-8") as file_obj:
            writer = csv.writer(file_obj)
            writer.writerow(
                [
                    row["timestamp"],
                    row["case_id"],
                    row["session_id"],
                    row["text_input"],
                    row["mri_description"],
                    row["image_name"],
                    row["image_size_bytes"],
                    row["case_summary"],
                    " | ".join(row["mri_interpretation"]),
                    " | ".join(row["safe_insights"]),
                    row["hospitals_count"],
                    " | ".join(row["tools_used"]),
                    row["disclaimer"],
                ]
            )
