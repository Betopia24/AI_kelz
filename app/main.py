from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from app.services.utils.ai_analysis import AIAnalyzer
from app.services.utils.transcription import VoiceTranscriber
from app.services.utils.document_ocr import DocumentOCR
import os
import tempfile
import shutil
from typing import Dict, Any

# Initialize FastAPI app
app = FastAPI(
    title="AI Analysis API",
    description="API for AI-powered analysis of documents, audio, and text files",
    version="1.0.0"
)

# Create main router
router = APIRouter()

# Initialize services
ai_analyzer = AIAnalyzer()
voice_transcriber = VoiceTranscriber()
document_ocr = DocumentOCR()

# Import and include routers
from app.services.deviation.incident import incident_router
from app.services.deviation.attchement.attachment_router import router as attachment_router
from app.services.initiation.initiation_route import router as initiation_router
from app.services.deviation.investigation.investigation_router import router as investigation_router
from app.services.deviation.quality_review.quality_review_router import router as quality_review_router
from app.services.QTA.QTA_revision.QTA_revision_router import router as qta_revision_router
from app.services.QTA.QTA_review.qta_review_router import router as qta_review_router
from app.services.deviation.Inverstigation_modify.Inverstigation_modify_route import router as investigation_modify_router
from app.services.deviation.incident_modify.incident_modify_router import router as incident_modify_router
from app.services.deviation.impact_assessment.impact_assessment_route import register_impact_assessment_routes

# Register incident routes
incident_router.register_incident_routes(router)

# Register impact assessment routes
register_impact_assessment_routes(router)

# Include file extract router under deviation tag
router.include_router(attachment_router, prefix="/Attachment", tags=["deviation"])
router.include_router(initiation_router, prefix="/initiation", tags=["deviation"])
router.include_router(investigation_router, prefix="/investigation/audio", tags=["deviation"])
router.include_router(investigation_modify_router, prefix="/deviation", tags=["deviation"])
router.include_router(incident_modify_router, prefix="/deviation", tags=["deviation"])

# Include quality review router
router.include_router(quality_review_router, prefix="/quality-review", tags=["deviation"])

# Include QTA revision router
router.include_router(qta_revision_router, tags=["qta-revision"])
router.include_router(qta_review_router, tags=["qta-review"])

# --- DEFAULT TAG ENDPOINTS ---
@router.post("/ai-analysis/", tags=["default"])
async def ai_analysis(file: UploadFile = File(...)):
    """AI analysis of uploaded text file."""
    try:
        # Validate file type
        if not file.content_type.startswith('text/'):
            raise HTTPException(status_code=400, detail="Only text files are supported")
        
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Perform AI analysis
        result = ai_analyzer.analyze_incident(text_content)
        
        if result:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "filename": file.filename,
                    "analysis": result,
                    "message": "AI analysis completed successfully"
                }
            )
        else:
            raise HTTPException(status_code=500, detail="AI analysis failed")
            
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please upload a UTF-8 text file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@router.post("/extract-text/", tags=["default"])
async def text_extraction(files: list[UploadFile] = File(...)):
    """Extract text from multiple uploaded files using OCR and conversion."""
    temp_file_paths = []
    try:
        # Save all uploaded files to temp and collect paths
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                temp_file_path = temp_file.name
                content = await file.read()
                temp_file.write(content)
                temp_file_paths.append(temp_file_path)
        # Extract text from all files
        results = document_ocr.extract_text_from_files(temp_file_paths)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "results": results,
                "message": "Text extraction completed for all files"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction error: {str(e)}")
    finally:
        # Clean up all temporary files
        for path in temp_file_paths:
            if os.path.exists(path):
                os.unlink(path)

@router.post("/transcription/audio/", tags=["default"])
async def transcription_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio file."""
    temp_file_path = None
    try:
        # Validate file type
        supported_audio_types = [
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 
            'audio/mp4', 'audio/webm', 'audio/ogg', 'audio/flac'
        ]
        
        if audio.content_type not in supported_audio_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio type: {audio.content_type}. Supported types: {', '.join(supported_audio_types)}"
            )
        
        # Check file size (25MB limit for OpenAI Whisper)
        content = await audio.read()
        if len(content) > 25 * 1024 * 1024:  # 25MB
            raise HTTPException(status_code=400, detail="Audio file too large (max 25MB)")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(content)
        
        # Transcribe audio
        original_transcription, polished_transcription = voice_transcriber.process_file_with_results(temp_file_path)
        
        if original_transcription:
            # Also perform AI analysis on the transcription
            incident_analysis = ai_analyzer.analyze_incident(original_transcription)
            summary_analysis = ai_analyzer.get_summary_analysis(original_transcription)
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "filename": audio.filename,
                    "original_transcription": original_transcription,
                    "polished_transcription": polished_transcription,
                    "incident_analysis": incident_analysis,
                    "summary": summary_analysis,
                    "transcription_length": len(original_transcription),
                    "message": "Audio transcription completed successfully"
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Audio transcription failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

# --- DEVIATION TAG ENDPOINTS ---



# Include the main router in the app
app.include_router(router)

# Root endpoints
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the AI Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "ai_analysis": "/ai-analysis/",
            "text_extraction": "/extract-text/",
            "transcription": "/transcription/audio/",
            "deviation_file_extract": "/deviation/file-extract",
            "deviation_investigation": "/deviation/investigation/",
            "deviation_quality_review": "/deviation/quality-review/",
            "capa_details": "/capa/details/",
            "capa_review": "/capa/review/",
            "capa_documents": "/capa/documents/",
            "incident_management": "/incident/",
            "qta_revision": "/qta-revision/"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running normally"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)