import time
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from app.services.QTA.QTA_revision.QTA_revision_schema import VoiceRevisionResponse, ErrorResponse, AIUpdateDocumentRequest, AIUpdateDocumentResponse
from app.services.QTA.QTA_revision.QTA_revision import VoiceRevisionService
from app.services.utils.ai_analysis import AIAnalyzer
from app.services.utils.document_ocr import DocumentOCR

router = APIRouter(prefix="/qta-revision", tags=["qta-revision"])
voice_service = VoiceRevisionService()
ai_analyzer = AIAnalyzer()
document_ocr = DocumentOCR()

@router.post("/process-voice", response_model=VoiceRevisionResponse)
async def process_voice_revision(
    audio_files: list[UploadFile] = File(None),
    documents: list[UploadFile] = File(None)
):
    """
    Process one or more voice audio files and (optionally) one or more document files. Returns transcribed text, bullet points, summary, and processed document text for each.
    """
    try:
        responses = []
        # Process multiple audio files
        if audio_files:
            for audio_file in audio_files:
                if not audio_file.content_type.startswith('audio/'):
                    responses.append({
                        "status": "error",
                        "filename": audio_file.filename,
                        "message": "Only audio files are allowed for audio_file parameter"
                    })
                    continue
                result = await voice_service.process_voice_file(audio_file)
                responses.append({
                    "status": "success",
                    "filename": audio_file.filename,
                    "transcribed_text_as_bullet_point": result["bullet_points"],
                    "summary": result["summary"],
                    "processed_document_text": None
                })
        # Process multiple document files
        if documents:
            for document in documents:
                import tempfile, os
                suffix = os.path.splitext(document.filename)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_doc:
                    temp_doc_path = temp_doc.name
                    content = await document.read()
                    temp_doc.write(content)
                try:
                    processed_document_text = document_ocr.process_file(temp_doc_path)
                except Exception as e:
                    processed_document_text = f"[ERROR] Could not extract text: {e}"
                finally:
                    if os.path.exists(temp_doc_path):
                        os.unlink(temp_doc_path)
                responses.append({
                    "status": "success",
                    "filename": document.filename,
                    "transcribed_text_as_bullet_point": None,
                    "summary": None,
                    "processed_document_text": processed_document_text
                })
        if not responses:
            return {"status": "error", "message": "No input files provided."}
        return {"results": responses}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice file: {str(e)}"
        )


@router.post("/ai-update-document", response_model=AIUpdateDocumentResponse)
async def ai_update_document(request: AIUpdateDocumentRequest):
    """
    Update the processed document text using AI based on the summary of required changes.
    """
    try:
        prompt = f"""
You are an expert in document editing. Here is a summary of required changes:
SUMMARY:
{request.summary}

Here is the original document text:
DOCUMENT:
{request.processed_document_text}

Please apply the changes described in the summary to the document text. Return only the updated document text.
"""
        updated_text = ai_analyzer.analyze_with_prompt(prompt)
        if not updated_text:
            raise HTTPException(status_code=500, detail="AI did not return an updated document text.")
        return AIUpdateDocumentResponse(updated_text=updated_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI document update failed: {str(e)}")

async def extract_document_text(document: UploadFile) -> str:
    """Extract text from uploaded document using local extraction methods"""
    import tempfile
    import os
    
    suffix = os.path.splitext(document.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_doc:
        temp_doc_path = temp_doc.name
        content = await document.read()
        temp_doc.write(content)
    
    try:
        def extract_text_local(file_path):
            import os
            ext = os.path.splitext(file_path)[1].lower()
            try:
                if ext == ".pdf":
                    from PyPDF2 import PdfReader
                    with open(file_path, "rb") as f:
                        reader = PdfReader(f)
                        text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    # If text is empty or whitespace, try OCR
                    if not text.strip():
                        try:
                            import fitz  # PyMuPDF
                            import pytesseract
                            from PIL import Image
                            ocr_text = []
                            with fitz.open(file_path) as doc:
                                for page_num in range(doc.page_count):
                                    page = doc.load_page(page_num)
                                    pix = page.get_pixmap()
                                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                    text = pytesseract.image_to_string(img)
                                    if text.strip():
                                        ocr_text.append(text)
                            text = "\n".join(ocr_text)
                        except Exception as ocr_e:
                            return f"[ERROR] PDF OCR failed: {ocr_e}"
                    return text
                elif ext == ".docx":
                    from docx import Document
                    doc = Document(file_path)
                    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                elif ext in [".txt", ".csv", ".md", ".log"]:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                else:
                    return "[ERROR] Unsupported file type for local extraction."
            except Exception as e:
                return f"[ERROR] Local extraction failed: {e}"
        
        processed_document_text = extract_text_local(temp_doc_path)
        return processed_document_text
        
    except Exception as e:
        return f"[ERROR] Could not extract text: {e}"
    finally:
        if os.path.exists(temp_doc_path):
            os.unlink(temp_doc_path)