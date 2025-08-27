"""
AI-powered modification of incident analysis responses.
Similar to investigation_modify: given an existing incident response and a user's instruction,
produce the same structure with only the requested modifications applied.
"""

from app.services.utils.ai_analysis import AIAnalyzer
import json
import re
from typing import Any, Dict


def get_system_prompt() -> str:
    return (
        "You are an AI assistant specialized in updating INCIDENT analysis documents. "
        "You will receive an existing incident response (as JSON) and a user's spoken instruction (as text). "
        "Your job is to modify ONLY the portion(s) of the incident response that the instruction requests, "
        "leaving the rest of the response unchanged. "
        "Respond ONLY with JSON. You may return either the full updated incident document or just the fields you changed. "
        "Do NOT include explanations or code fences."
    )


# Utilities to parse and merge AI output safely

def extract_json_from_text(text: str) -> str:
    """Extract JSON content from raw model output, handling optional code fences."""
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1].strip()
    return text.strip()


def parse_ai_json(ai_str: str):
    """Parse AI output into a JSON object if possible, else return None."""
    cleaned = extract_json_from_text(ai_str)
    try:
        return json.loads(cleaned)
    except Exception:
        return None


def deep_merge_dict(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge updates into base. Lists and scalars are replaced; dicts are merged."""
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = deep_merge_dict(dict(base[k]), v)
        else:
            base[k] = v
    return base


def generate_modified_incident(incident_response: dict, instruction_text: str) -> dict:
    """
    Uses the OpenAI-powered AIAnalyzer to generate a modified incident response
    based on the user's instruction and the current response dict. Returns the
    same shape as the input with only the requested changes applied.
    """
    system_prompt = get_system_prompt()
    full_prompt = (
        f"System: {system_prompt}\n\n"
        f"Current Incident Analysis Document (JSON):\n{json.dumps(incident_response, indent=2)}\n\n"
        f"User Instruction for Modification:\n{instruction_text}\n\n"
        f"Return ONLY the updated incident JSON. You may return either the full document or just the fields you changed. Do not include code fences."
    )

    analyzer = AIAnalyzer()
    ai_result_str = analyzer.analyze_with_prompt(full_prompt)

    # Deep copy of original
    base_copy: Dict[str, Any] = json.loads(json.dumps(incident_response))

    ai_updates = parse_ai_json(ai_result_str)
    if ai_updates and isinstance(ai_updates, dict):
        merged = deep_merge_dict(base_copy, ai_updates)
        return merged

    # Fallback to original if parsing failed
    return base_copy
