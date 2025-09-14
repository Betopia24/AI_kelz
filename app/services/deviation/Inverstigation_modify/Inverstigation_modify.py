"""
AI-powered modification of investigation responses. Uses OpenAI LLM via AIAnalyzer, with a system prompt instructing it
to ONLY change the part(s) of the response as requested by the user's instruction.
"""

from app.services.utils.ai_analysis import AIAnalyzer
import json
import re
from typing import Any, Dict

def get_system_prompt():
    return (
        "You are an AI assistant specialized in updating investigation documents. "
        "You will receive an existing investigation response (as JSON) and a user's spoken instruction (as text). "
        "Your job is to modify ONLY the portion(s) of the investigation response that the instruction requests, "
        "leaving the rest of the response unchanged. "
        "Respond ONLY with JSON. You may return either the full updated investigation document or just the fields you changed. "
        "Do NOT include explanations or code fences."
    )

# Helper utilities to parse and merge AI output safely

def extract_json_from_text(text: str) -> str:
    """Extract JSON content from raw model output, handling optional code fences."""
    # Handle ```json ... ``` or ``` ... ``` blocks
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Fallback: take content between first { and last }
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


def generate_modified_investigation(investigation_response: dict, instruction_text: str) -> dict:
    """
    Uses the OpenAI-powered AIAnalyzer to generate a modified investigation response
    based on the user's instruction and the current response dict.
    """
    system_prompt = get_system_prompt()
    # Compose the full prompt for the LLM
    full_prompt = (
        f"System: {system_prompt}\n\n"
        f"Current Investigation Document (JSON):\n{json.dumps(investigation_response, indent=2)}\n\n"
        f"User Instruction for Modification:\n{instruction_text}\n\n"
        f"Return ONLY the updated investigation JSON. You may return either the full document or just the fields you changed. Do not include code fences."
    )
    analyzer = AIAnalyzer()
    ai_result_str = analyzer.analyze_with_prompt(full_prompt)

    # Parse and deep-merge AI changes into the original investigation shape
    base_copy: Dict[str, Any] = json.loads(json.dumps(investigation_response))  # deep copy
    ai_updates = parse_ai_json(ai_result_str)
    if ai_updates and isinstance(ai_updates, dict):
        merged = deep_merge_dict(base_copy, ai_updates)
        return merged

    # Fallback: return the original investigation unchanged
    return base_copy
