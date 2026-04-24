import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def load_project_env() -> None:
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / '.env'
    if not env_path.exists():
        return
    if load_dotenv is not None:
        load_dotenv(env_path, override=True)
        key = os.getenv('OPENAI_API_KEY')
        if key is not None:
            os.environ['OPENAI_API_KEY'] = key.strip().strip('\"').strip("'")
        return

    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_project_env()


class CaseCSVStore:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        if not os.path.exists(csv_path):
            with open(csv_path, 'w', newline='', encoding='utf-8') as file_obj:
                writer = csv.writer(file_obj)
                writer.writerow([
                    'timestamp',
                    'case_id',
                    'session_id',
                    'text_input',
                    'mri_description',
                    'image_name',
                    'image_size_bytes',
                    'case_summary',
                    'mri_interpretation',
                    'safe_insights',
                    'hospitals_count',
                    'tools_used',
                    'tool_decisions',
                    'disclaimer',
                ])

    def save(self, row: Dict[str, Any]) -> None:
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as file_obj:
            writer = csv.writer(file_obj)
            writer.writerow([
                row.get('timestamp', ''),
                row.get('case_id', ''),
                row.get('session_id', ''),
                row.get('text_input', ''),
                row.get('mri_description', ''),
                row.get('image_name', ''),
                row.get('image_size_bytes', 0),
                row.get('case_summary', ''),
                ' | '.join(row.get('mri_interpretation', [])),
                ' | '.join(row.get('safe_insights', [])),
                row.get('hospitals_count', 0),
                ' | '.join(row.get('tools_used', [])),
                json.dumps(row.get('tool_decisions', {}), ensure_ascii=False),
                row.get('disclaimer', ''),
            ])


def as_json_string(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def try_load_json(value: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


def flatten_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    parts.append(str(item.get('text', '')))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return '\n'.join(part for part in parts if part)
    return str(content)
