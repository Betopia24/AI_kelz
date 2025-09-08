from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from app.services.deviation.incident_modify.incident_modify import (
    generate_modified_incident, 
    parse_input_data, 
    classify_modification_type,
    validate_modification_result
)
from app.services.utils.transcription import transcribe_audio
import json
import os
import tempfile

router = APIRouter()


@router.post("/incident-modify-with-audio", tags=["deviation"])
async def incident_modify_with_audio(
    incident_response: str = Body(..., embed=True, description="Original incident response (JSON string)"),
    impact_assessment: str = Body(..., embed=True, description="Impact assessment response (JSON string)"),
    instruction_audio: UploadFile = File(..., description="Audio file with modify instruction")
):
    """
    Takes the original incident response, impact assessment response, and a voice instruction (audio file),
    transcribes the instruction, and returns the AI-modified incident response.
    The output preserves the original incident response structure, applying only the requested changes.
    """
    print("=== INCIDENT MODIFY DEBUG START ===")

    # Robustly parse both incident_response and impact_assessment (accept JSON or structured text)
    try:
        response_dict = parse_input_data(incident_response)
        print(f"DEBUG - Parsed incident response with keys: {list(response_dict.keys())}")
    except Exception as e:
        print(f"DEBUG - Failed to parse incident_response: {e}")
        raise HTTPException(status_code=400, detail="Invalid format for incident_response.")
    
    try:
        impact_dict = parse_input_data(impact_assessment)
        print(f"DEBUG - Parsed impact assessment with keys: {list(impact_dict.keys())}")
    except Exception as e:
        print(f"DEBUG - Failed to parse impact_assessment: {e}")
        raise HTTPException(status_code=400, detail="Invalid format for impact_assessment.")

    # Store original for comparison
    original_response = dict(response_dict)

    # Merge the two for context (add impact assessment under a new key)
    merged_dict = dict(response_dict)
    merged_dict["impact_assessment"] = impact_dict

    temp_file_path = None
    try:
        # Save uploaded audio to a temporary file
        content = await instruction_audio.read()
        if not content:
            raise ValueError("Empty audio file")
        suffix = os.path.splitext(instruction_audio.filename)[1] or ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_file_path = tmp.name
        # Transcribe using local transcriber that expects a file path
        instruction_text = transcribe_audio(temp_file_path)
        if not instruction_text:
            raise ValueError("Transcription returned empty result")
        print(f"DEBUG - Transcribed instruction: '{instruction_text}'")
        
        # Classify the modification type
        modification_type = classify_modification_type(instruction_text)
        print(f"DEBUG - Detected modification type: {modification_type}")
        
    except Exception as exc:
        print(f"DEBUG - Audio transcription failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {exc}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

    # Show relevant fields before modification (current state)
    print("DEBUG - Key fields BEFORE this modification (current state):")
    current_incident_data = {k: v for k, v in merged_dict.items() if k != "impact_assessment"}
    for k, v in current_incident_data.items():
        if any(keyword in k.lower() for keyword in ['title', 'background', 'analysis', 'assessment']):
            display_value = str(v)[:200] + "..." if len(str(v)) > 200 else str(v)
            print(f"  Field '{k}': {display_value}")

    # Get the modified incident response from the system
    try:
        print(f"DEBUG - Applying {modification_type} modification using AI (preserving current state)")
        modified_response = generate_modified_incident(merged_dict, instruction_text)
        
        # The modified_response should now contain both incident and impact assessment data
        # with the new modification applied on top of the current state
        
        # Validate the modification
        # Compare only the incident part (excluding impact_assessment)
        new_incident_part = {k: v for k, v in modified_response.items() if k != "impact_assessment"}
        validation_passed = validate_modification_result(current_incident_data, new_incident_part, instruction_text)
        if not validation_passed:
            print("DEBUG - Modification validation failed, but proceeding")
        
        # Show key fields after modification to verify changes
        print("DEBUG - Key fields AFTER this modification:")
        for k, v in modified_response.items():
            if k == "impact_assessment":
                print(f"  Field '{k}': [Impact Assessment Data Preserved]")
            elif any(keyword in k.lower() for keyword in ['title', 'background', 'analysis', 'assessment']):
                display_value = str(v)[:200] + "..." if len(str(v)) > 200 else str(v)
                print(f"  Field '{k}': {display_value}")
        
        # Show what actually changed in this modification
        print("DEBUG - Fields changed in this modification:")
        changes_found = False
        for k in current_incident_data.keys():
            if k in new_incident_part and current_incident_data[k] != new_incident_part[k]:
                print(f"  Changed field '{k}':")
                print(f"    BEFORE: {str(current_incident_data[k])[:100]}...")
                print(f"    AFTER:  {str(new_incident_part[k])[:100]}...")
                changes_found = True
        
        if not changes_found:
            print("  No changes detected in this modification")
        
        # Ensure we always return the complete merged structure with cumulative changes
        print(f"DEBUG - Final output contains keys: {list(modified_response.keys())}")
        print("DEBUG - This output preserves ALL previous modifications plus the new one")
        
    except Exception as exc:
        print(f"DEBUG - AI modification failed: {exc}")
        # Even on failure, return the current state (which preserves previous modifications)
        print("DEBUG - Returning current state due to AI failure (preserves previous modifications)")
        return JSONResponse(status_code=200, content=merged_dict)

    print("=== INCIDENT MODIFY DEBUG END ===")
    return JSONResponse(status_code=200, content=modified_response)