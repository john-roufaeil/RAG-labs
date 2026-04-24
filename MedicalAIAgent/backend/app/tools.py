import csv
import os
import requests
from typing import List, Dict

def should_use_search_tool(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ["hospital", "nearby", "nearest", "clinic", "emergency"])

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
                out.append({
                    "name": item.get("name") or item.get("display_name", "Hospital").split(",")[0],
                    "address": item.get("display_name", "Address unavailable"),
                    "lat": float(item["lat"]),
                    "lon": float(item["lon"]),
                })
            return out
        except Exception:
            return []

class CSVStorageTool:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "case_id", "session_id", "text_input", "mri_description",
                    "image_name", "image_size_bytes", "case_summary", "safe_insights",
                    "hospitals_count", "tools_used", "disclaimer"
                ])

    def save(self, row: Dict):
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                row["timestamp"], row["case_id"], row["session_id"], row["text_input"],
                row["mri_description"], row["image_name"], row["image_size_bytes"],
                row["case_summary"], " | ".join(row["safe_insights"]), row["hospitals_count"],
                " | ".join(row["tools_used"]), row["disclaimer"]
            ])
