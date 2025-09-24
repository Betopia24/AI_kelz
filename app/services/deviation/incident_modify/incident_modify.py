"""
AI-powered modification of incident analysis responses.
Similar to investigation_modify: given an existing incident response and a user's instruction,
produce the same structure with only the requested modifications applied.
"""

from app.services.utils.ai_analysis import AIAnalyzer
import json
import re
from typing import Any, Dict, Union


def get_system_prompt() -> str:
    return (
        "You are an AI assistant specialized in updating INCIDENT analysis documents. "
        "You will receive document data (as JSON) and a user's spoken instruction (as text). "
        "Your job is to modify ONLY the portion(s) that the instruction requests, "
        "leaving the rest unchanged. "
        "IMPORTANT: You must preserve the exact original structure and field names. "
        
        "CRITICAL FOR CUMULATIVE MODIFICATIONS: "
        "The document data you receive represents the CURRENT STATE, which may already contain "
        "previous modifications made by earlier user instructions. You MUST preserve ALL existing "
        "content and previous changes while applying only the new requested modification. "
        "This ensures that all modifications are cumulative and build upon each other. "
        
        "Instructions for different types of modifications: "
        "1. TITLE CHANGES: When asked to change/update title, look for fields containing 'TITLE' or 'title' "
        "   and update appropriately (structured or simple fields) "
        "2. CONTENT ADDITIONS: When asked to add information, append to existing relevant fields "
        "3. CONTENT MODIFICATIONS: When asked to change specific content, update only those parts "
        "4. CONTENT REMOVAL: When asked to remove something, delete only the specified content "
        "5. FIELD UPDATES: When asked to update specific fields, modify only those fields "
        
        "CRITICAL RULES: "
        "- Return the COMPLETE JSON structure with ALL original fields "
        "- Preserve ALL original field names and structure exactly "
        "- PRESERVE ALL PREVIOUS MODIFICATIONS - do not revert any earlier changes "
        "- Only modify what the user specifically requests in this current instruction "
        "- For structured text fields (like 'FIELD_NAME: content'), maintain the format "
        "- When updating nested content, preserve the surrounding context "
        "- Make changes proportional to the request (small changes for small requests) "
        "- Do NOT remove or ignore any fields from the current structure "
        "- Think of this as applying a new layer of changes on top of the current state "
        
        "MERGE REQUIREMENT: "
        "The output must be a complete structure containing both the incident data "
        "(with ALL previous modifications preserved plus the new requested change) "
        "and any impact assessment data (unchanged). "
        
        "Respond ONLY with the complete updated JSON structure. "
        "Do NOT include explanations or code fences."
    )


def parse_incident_output(incident_str: str) -> Dict[str, Any]:
    """
    Parse the incident output string format into a dictionary.
    Expected format: FIELD_NAME: value
    """
    incident_dict = {}
    lines = incident_str.strip().split('\n')
    
    current_field = None
    current_value = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('-'):  # Skip empty lines and separator lines
            continue
            
        # Check if line starts with a field name (contains colon and is uppercase)
        if ':' in line and line.split(':')[0].strip().isupper():
            # Save previous field if exists
            if current_field:
                incident_dict[current_field] = '\n'.join(current_value).strip()
            
            # Start new field
            parts = line.split(':', 1)
            current_field = parts[0].strip()
            current_value = [parts[1].strip()] if len(parts) > 1 and parts[1].strip() else []
        else:
            # Continuation of current field
            if current_field:
                current_value.append(line)
    
    # Don't forget the last field
    if current_field:
        incident_dict[current_field] = '\n'.join(current_value).strip()
    
    return incident_dict


def parse_impact_assessment_output(impact_str: str) -> Dict[str, Any]:
    """
    Parse the impact assessment output string format into a dictionary.
    Handles both simple key:value pairs and JSON objects.
    """
    impact_dict = {}
    lines = impact_str.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('-'):  # Skip empty lines and separator lines
            continue
            
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Try to parse as JSON if it looks like a JSON object
            if value.startswith('{') and value.endswith('}'):
                try:
                    impact_dict[key] = json.loads(value)
                except json.JSONDecodeError:
                    impact_dict[key] = value
            else:
                impact_dict[key] = value
    
    return impact_dict


def parse_input_data(data: Union[str, dict]) -> Dict[str, Any]:
    """
    Parse input data whether it's a JSON string, structured text, or already a dict.
    """
    if isinstance(data, dict):
        return data
    
    if isinstance(data, str):
        # First try to parse as JSON
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            # If JSON parsing fails, check if it looks like incident output format
            if 'INCIDENT_TITLE:' in data or 'BACKGROUND:' in data:
                return parse_incident_output(data)
            # Or impact assessment format
            elif 'DEVIATION_TRIAGE:' in data or 'PRODUCT_QUALITY:' in data:
                return parse_impact_assessment_output(data)
            else:
                # Generic field:value parsing
                result = {}
                for line in data.split('\n'):
                    line = line.strip()
                    if ':' in line and not line.startswith('-'):
                        key, value = line.split(':', 1)
                        result[key.strip()] = value.strip()
                return result if result else {"content": data}
    
    return {"content": str(data)}


def classify_modification_type(instruction_text: str) -> str:
    """
    Classify the type of modification being requested
    """
    instruction_lower = instruction_text.lower().strip()
    
    # Title-specific keywords
    if any(keyword in instruction_lower for keyword in ['title', 'name it', 'rename', 'call it']):
        return "title_change"
    
    # Addition keywords
    elif any(keyword in instruction_lower for keyword in ['add', 'include', 'append', 'insert']):
        return "content_addition"
    
    # Removal keywords  
    elif any(keyword in instruction_lower for keyword in ['remove', 'delete', 'take out', 'eliminate']):
        return "content_removal"
    
    # Modification keywords
    elif any(keyword in instruction_lower for keyword in ['change', 'update', 'modify', 'edit', 'replace']):
        return "content_modification"
    
    # Default to general modification
    return "general_modification"


def extract_json_from_text(text: str) -> str:
    """Extract JSON content from raw model output, handling optional code fences."""
    # Remove any markdown code fences
    text = re.sub(r'```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```', '', text)
    
    # Try to find JSON boundaries
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1].strip()
    
    return text.strip()


def parse_ai_json(ai_str: str):
    """Parse AI output into a JSON object if possible. If that fails, use a fallback
    regex-based extraction of simple string key-value pairs to salvage updates like title changes.
    """
    cleaned = extract_json_from_text(ai_str)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"DEBUG - JSON parsing error: {e}")
        print(f"DEBUG - Cleaned text: {cleaned[:500]}...")
        # Fallback: extract simple "key": "value" pairs to recover partial updates (e.g., title changes)
        try:
            # Match JSON-like string pairs, tolerating escaped quotes inside values
            pairs = re.findall(r'"([^"\\]+)"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, flags=re.DOTALL)
            fallback: Dict[str, Any] = {}
            for k, v in pairs:
                # Unescape common sequences (simple heuristic)
                try:
                    v_unescaped = bytes(v, 'utf-8').decode('unicode_escape')
                except Exception:
                    v_unescaped = v
                fallback[k] = v_unescaped
            if fallback:
                print(f"DEBUG - Fallback parser extracted keys: {list(fallback.keys())}")
                return fallback
        except Exception as ie:
            print(f"DEBUG - Fallback extraction error: {ie}")
        return None


def smart_merge_dict(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intelligently merge updates into base, handling nested structures properly.
    """
    result = json.loads(json.dumps(base))  # Deep copy
    
    for key, value in updates.items():
        if key in result:
            if isinstance(value, dict) and isinstance(result[key], dict):
                # Recursively merge nested dictionaries
                result[key] = smart_merge_dict(result[key], value)
            else:
                # Replace with new value
                result[key] = value
        else:
            # New field, add it
            result[key] = value
    
    return result


def generate_modified_incident(incident_response: Union[str, dict], instruction_text: str) -> dict:
    """
    Uses the OpenAI-powered AIAnalyzer to generate a modified incident response
    based on the user's instruction and the current response dict. Returns the
    same shape as the input with only the requested changes applied.
    """
    # Parse the incident response into a dictionary
    if isinstance(incident_response, str):
        parsed_incident = parse_input_data(incident_response)
    else:
        parsed_incident = incident_response
    
    # DEBUG: Print the structure and instruction type
    modification_type = classify_modification_type(instruction_text)
    print(f"DEBUG - Original incident keys: {list(parsed_incident.keys())}")
    print(f"DEBUG - Instruction: '{instruction_text}'")
    print(f"DEBUG - Modification type: {modification_type}")
    
    # Create a more specific system prompt based on modification type
    base_system_prompt = get_system_prompt()
    
    if modification_type == "title_change":
        specific_instruction = (
            "USER IS REQUESTING A TITLE CHANGE. "
            "Look for fields containing 'title' or 'TITLE' and update them appropriately. "
            "For structured fields like 'INCIDENT_TITLE: Old Title', replace only the title part. "
            "Generate a professional, descriptive title based on the incident content."
        )
    elif modification_type == "content_addition":
        specific_instruction = (
            "USER IS REQUESTING TO ADD CONTENT. "
            "Find the most appropriate existing field(s) and add the requested information. "
            "Maintain the original structure and formatting."
        )
    elif modification_type == "content_removal":
        specific_instruction = (
            "USER IS REQUESTING TO REMOVE CONTENT. "
            "Identify and remove only the specific content mentioned. "
            "Keep all other content intact."
        )
    elif modification_type == "content_modification":
        specific_instruction = (
            "USER IS REQUESTING TO MODIFY EXISTING CONTENT. "
            "Update only the specific parts mentioned in the instruction. "
            "Preserve the overall structure and other content."
        )
    else:
        specific_instruction = (
            "USER IS REQUESTING A GENERAL MODIFICATION. "
            "Carefully analyze the instruction and apply only the requested changes."
        )
    
    full_prompt = (
        f"System: {base_system_prompt}\n\n"
        f"SPECIFIC CONTEXT: {specific_instruction}\n\n"
        f"Current Incident Analysis Document (JSON):\n{json.dumps(parsed_incident, indent=2)}\n\n"
        f"User Instruction for Modification:\n{instruction_text}\n\n"
        f"IMPORTANT: Return ONLY the complete updated JSON structure with the same field names and structure. "
        f"Apply ONLY the changes requested in the user instruction. Do not make any other modifications."
    )

    analyzer = AIAnalyzer()
    ai_result_str = analyzer.analyze_with_prompt(full_prompt)
    
    # DEBUG: Print what the AI returned
    print(f"DEBUG - AI raw response (first 500 chars): {ai_result_str[:500]}...")

    # Parse AI response
    ai_updates = parse_ai_json(ai_result_str)
    
    if ai_updates and isinstance(ai_updates, dict):
        print(f"DEBUG - Successfully parsed AI response with keys: {list(ai_updates.keys())}")
        
        # Validate that the AI response has the expected structure
        if set(ai_updates.keys()) == set(parsed_incident.keys()):
            print("DEBUG - AI response maintains original structure")
            return ai_updates
        else:
            print("DEBUG - AI response structure differs from original, attempting smart merge")
            merged = smart_merge_dict(parsed_incident, ai_updates)
            return merged
    else:
        print("DEBUG - Failed to parse AI response, returning original")
        return parsed_incident


def validate_modification_result(original: dict, modified: dict, instruction: str) -> bool:
    """
    Validate that the modification was applied correctly
    """
    # Basic validation - structure should be preserved
    if set(original.keys()) != set(modified.keys()):
        print("DEBUG - Warning: Field structure changed during modification")
        return False
    
    # Check if anything actually changed
    if original == modified:
        print("DEBUG - Warning: No changes detected after modification")
        return False
    
    return True