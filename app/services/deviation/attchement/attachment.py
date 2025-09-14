import json
import re
from typing import List, Dict, Optional
import docx
import PyPDF2
import io
import os
from pathlib import Path
import requests
from dataclasses import dataclass

# Import existing services
from app.services.utils.transcription import VoiceTranscriber


@dataclass
class DocumentInfo:
    """Data class to hold document information"""
    filename: str
    extracted_text: str
    file_size: int
    page_count: int = 1


class AIDocumentAnalysisService:
    """
    Enhanced document analysis service that uses OpenAI for intelligent
    categorization and title generation
    """
    
    def __init__(self, openai_api_key: str):
        """Initialize with OpenAI API key"""
        self.openai_api_key = openai_api_key
        self.voice_transcriber = VoiceTranscriber()
        
        # Fallback to emergency service if AI fails
        self.emergency_service = EmergencyFileExtractService()
    
    def call_openai_api(self, messages: List[Dict], max_tokens: int = 1500) -> Optional[str]:
        """
        Call OpenAI API with error handling
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-4o-mini',  # Using cost-effective model
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': 0.3  # Lower temperature for more consistent results
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return None
                
        except Exception as e:
            return None
    
    def extract_text_directly(self, file_path: str) -> str:
        """
        Direct text extraction (same as emergency service)
        """
        return self.emergency_service.extract_text_directly(file_path)
    
    def classify_document_with_ai(self, text: str, filename: str = "") -> Dict:
        """
        Use OpenAI to intelligently classify document and generate title
        """
        # Truncate text if too long (to stay within token limits)
        max_chars = 8000  # Roughly 2000 tokens
        if len(text) > max_chars:
            text = text[:max_chars] + "... [content truncated]"
        
        system_prompt = """You are an expert document classifier. Analyze the given document text and classify it into one of these categories:

1. Batch_records - Production batch records, lot records, manufacturing logs
2. SOP_s - Standard Operating Procedures, work instructions, process methods
3. Forms - Forms, templates, checklists, inspection sheets
4. Interviews - Interview transcripts, meeting minutes, Q&A sessions
5. Logbooks - Daily logs, shift reports, maintenance logs, equipment logs
6. Email_references - Email communications, correspondence
7. Certificates - Certificates, training records, qualifications

Respond with a JSON object containing:
- "category": the most appropriate category from the list above
- "confidence": confidence score from 0-100
- "title": a descriptive title for this document (2-8 words)
- "reasoning": brief explanation of your classification
- "key_content": 2-3 key points or phrases that support your classification

Be precise and professional in your analysis."""

        user_prompt = f"""Document filename: {filename}

Document content:
{text}

Please classify this document and provide the requested JSON response."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.call_openai_api(messages, max_tokens=500)
        
        if response:
            try:
                # Try to extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Fallback to rule-based classification
        category = self.emergency_service.classify_document_content(text, filename)
        return {
            "category": category,
            "confidence": 60,
            "title": f"{category.replace('_', ' ').title()} Document",
            "reasoning": "Fallback rule-based classification",
            "key_content": ["Rule-based analysis", "Content classified automatically"]
        }
    
    def extract_and_analyze(self, file_path: str) -> dict:
        """
        Enhanced version that uses AI for analysis
        """
        # Extract text directly
        extracted_text = self.extract_text_directly(file_path)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            return {
                "error": "No text could be extracted from the document.",
                "extracted_text": "",
                "document_analysis": {},
            }
        
        # Use AI to classify document
        filename = Path(file_path).name
        ai_analysis = self.classify_document_with_ai(extracted_text, filename)
        
        category = ai_analysis.get("category", "Forms")
        title = ai_analysis.get("title", "Document")
        reasoning = ai_analysis.get("reasoning", "AI analysis")
        key_content = ai_analysis.get("key_content", [])
        
        # Create analysis result
        document_analysis = {
            "AI suggested Title": title,
            "Category": category,
            "Confidence": ai_analysis.get("confidence", 0),
            "Reasoning": reasoning,
            "Key Content": "; ".join(key_content) if key_content else "No key content identified"
        }
        
        # Add category-specific content
        for cat in ["Batch_records", "SOP_s", "Forms", "Interviews", "Logbooks", "Email_references", "Certificates"]:
            if cat == category:
                document_analysis[cat] = "; ".join(key_content[:3]) if key_content else "Content identified"
            else:
                document_analysis[cat] = "Not found in document"
        
        return {
            "extracted_text": extracted_text,
            "document_analysis": document_analysis
        }
    
    def match_files_with_voice_titles(self, files_info: List[Dict], voice_transcription: str) -> Dict:
        """
        Use AI to intelligently match files with voice-provided titles
        """
        if not voice_transcription or not voice_transcription.strip():
            return self.categorize_files_without_voice(files_info)
        
        # Prepare file information for AI
        files_summary = []
        for idx, file_info in enumerate(files_info):
            files_summary.append({
                "index": idx,
                "filename": file_info.get("filename", ""),
                "category": file_info.get("category", "Unknown"),
                "key_content": file_info.get("key_content", "")[:200]  # First 200 chars
            })
        
        system_prompt = """You are an expert at matching voice-provided titles to documents. 

The user has uploaded multiple files and provided voice input describing titles/names for these files. Your job is to intelligently match each file to the appropriate title from the voice input.

Respond with a JSON object containing:
- "overall_title": A descriptive title for the entire collection
- "file_mappings": Array of objects with:
  - "file_index": index of the file (0, 1, 2...)
  - "matched_title": the title from voice input that best matches this file
  - "confidence": confidence score 0-100
  - "reasoning": why this title matches this file

Be intelligent about matching - consider:
- File content and category
- Sequence/order mentioned in voice
- Keywords and context clues
- Partial matches and synonyms"""

        user_prompt = f"""Voice transcription from user: "{voice_transcription}"

Files to match:
{json.dumps(files_summary, indent=2)}

Please provide the JSON response matching files to voice titles."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.call_openai_api(messages, max_tokens=1000)
        
        if response:
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    ai_result = json.loads(json_str)
                    
                    # Format the result
                    file_mappings = []
                    for mapping in ai_result.get("file_mappings", []):
                        file_idx = mapping.get("file_index", 0)
                        if file_idx < len(files_info):
                            file_mappings.append({
                                "filename": files_info[file_idx].get("filename", ""),
                                "category": files_info[file_idx].get("category", "Unknown"),
                                "voice_title": mapping.get("matched_title", "Untitled"),
                                "confidence": mapping.get("confidence", 0),
                                "reasoning": mapping.get("reasoning", "AI matching")
                            })
                    
                    return {
                        "AI_suggested_Title": ai_result.get("overall_title", "Document Collection"),
                        "file_mappings": file_mappings
                    }
                    
            except json.JSONDecodeError as e:
                pass
        
        # Fallback to emergency service
        return self.emergency_service.categorize_files_with_voice_titles(files_info, voice_transcription)
    
    def categorize_files_without_voice(self, files_info: List[Dict]) -> Dict:
        """
        Categorize files when no voice input is provided
        """
        file_mappings = []
        categories_found = []
        
        for file_info in files_info:
            category = file_info.get("category", "Forms")
            categories_found.append(category)
            
            file_mappings.append({
                "filename": file_info.get("filename", ""),
                "category": category,
                "voice_title": file_info.get("title", "Auto-generated Title"),
                "confidence": file_info.get("confidence", 70),
                "reasoning": "No voice input provided, using AI-generated title"
            })
        
        # Generate overall title
        unique_categories = list(set(categories_found))
        if len(unique_categories) == 1:
            title_map = {
                "Batch_records": "Batch Production Documents",
                "SOP_s": "Standard Operating Procedures",
                "Forms": "Form Collection",
                "Interviews": "Interview Records",
                "Logbooks": "Log Records",
                "Email_references": "Email Communications",
                "Certificates": "Certificate Collection"
            }
            overall_title = title_map.get(unique_categories[0], "Document Collection")
        else:
            overall_title = f"Mixed Document Collection ({len(files_info)} files)"
        
        return {
            "AI_suggested_Title": overall_title,
            "file_mappings": file_mappings
        }

    def process_files_with_voice_input(self, file_paths: List[str], audio_file_path: str = None) -> Dict:
        """
        Complete workflow: process files and match with voice input
        """
        # Step 1: Process each file
        files_info = []
        for file_path in file_paths:
            try:
                result = self.extract_and_analyze(file_path)
                if "error" not in result:
                    analysis = result["document_analysis"]
                    files_info.append({
                        "filename": Path(file_path).name,
                        "category": analysis.get("Category", "Forms"),
                        "title": analysis.get("AI suggested Title", "Document"),
                        "confidence": analysis.get("Confidence", 70),
                        "key_content": analysis.get("Key Content", ""),
                        "text": result["extracted_text"]
                    })
                else:
                    continue  # Skip failed files
            except Exception as e:
                continue  # Skip files that cause exceptions
        
        if not files_info:
            return {"error": "No files could be processed successfully"}
        
        # Step 2: Transcribe voice input if provided
        voice_transcription = ""
        if audio_file_path and os.path.exists(audio_file_path):
            voice_transcription = self.voice_transcriber.transcribe_audio(audio_file_path)
            if not voice_transcription:
                voice_transcription = ""
        
        # Step 3: Match files with voice titles
        result = self.match_files_with_voice_titles(files_info, voice_transcription)
        
        # Add summary information
        result["processing_summary"] = {
            "total_files_processed": len(files_info),
            "voice_input_provided": bool(voice_transcription),
            "voice_transcription": voice_transcription if voice_transcription else "No voice input provided"
        }
        
        return result


# Keep the original emergency service as fallback
class EmergencyFileExtractService:
    """
    Emergency version that works even when OCR and AI services fail
    """
    
    @staticmethod
    def extract_text_directly(file_path: str) -> str:
        """
        Direct text extraction without relying on external OCR service
        """
        try:
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            if extension == '.pdf':
                return EmergencyFileExtractService._extract_pdf_text(file_path)
            elif extension == '.docx':
                return EmergencyFileExtractService._extract_docx_text(file_path)
            elif extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return ""
                
        except Exception as e:
            return ""
    
    @staticmethod
    def _extract_pdf_text(file_path: Path) -> str:
        """Extract text from PDF using PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                
                return '\n'.join(text_parts)
        except Exception as e:
            return ""
    
    @staticmethod
    def _extract_docx_text(file_path: Path) -> str:
        """Extract text from DOCX using python-docx"""
        try:
            doc = docx.Document(file_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return '\n'.join(text_parts)
        except Exception as e:
            return ""

    @staticmethod
    def classify_document_content(text: str, filename: str = "") -> str:
        """
        Advanced rule-based classification that actually works
        """
        if not text or len(text.strip()) < 10:
            return "Forms"  # Default for empty/minimal content
        
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Enhanced keyword scoring system
        category_indicators = {
            "Batch_records": {
                "strong": ["batch number", "lot number", "batch id", "lot id", "production date", 
                          "batch size", "manufacturing date", "yield", "batch record", "lot record"],
                "medium": ["batch", "lot", "production", "manufacturing", "yield %", "quantity produced"],
                "weak": ["produced", "manufactured", "date of production"]
            },
            "SOP_s": {
                "strong": ["standard operating procedure", "sop number", "procedure number", 
                          "work instruction", "operating instruction", "method number"],
                "medium": ["procedure", "protocol", "method", "instruction", "step 1", "step 2", 
                          "process description"],
                "weak": ["steps", "process", "operation", "technique"]
            },
            "Forms": {
                "strong": ["form number", "form id", "template", "checklist", "inspection form",
                          "fill in", "complete this form", "signature required"],
                "medium": ["form", "checklist", "inspection", "check one", "mark appropriate",
                          "date:", "name:", "signature:", "approved by"],
                "weak": ["fill", "complete", "check", "select", "choose"]
            },
            "Interviews": {
                "strong": ["interview transcript", "interview record", "meeting minutes",
                          "interviewee:", "interviewer:", "q:", "a:"],
                "medium": ["interview", "discussion", "conversation", "dialogue", "meeting",
                          "question", "answer", "response"],
                "weak": ["asked", "replied", "stated", "mentioned"]
            },
            "Logbooks": {
                "strong": ["daily log", "shift log", "maintenance log", "equipment log",
                          "logbook entry", "recorded by", "shift report"],
                "medium": ["log entry", "daily record", "shift", "maintenance", "equipment",
                          "time:", "logged", "recorded"],
                "weak": ["daily", "entry", "record", "noted"]
            },
            "Email_references": {
                "strong": ["from:", "to:", "subject:", "sent:", "received:", "cc:", "bcc:",
                          "email address", "reply", "forward"],
                "medium": ["email", "message", "correspondence", "communication",
                          "dear", "sincerely", "regards", "best regards"],
                "weak": ["sent", "received", "message", "communication"]
            },
            "Certificates": {
                "strong": ["certificate of", "certification", "certified that", "has completed",
                          "training certificate", "completion certificate", "qualified"],
                "medium": ["certificate", "training", "completion", "qualification", "accredited",
                          "issued by", "valid until", "expires"],
                "weak": ["certified", "completed", "qualified", "training"]
            }
        }
        
        # Calculate weighted scores
        scores = {}
        for category, indicators in category_indicators.items():
            score = 0
            
            # Strong indicators (weight: 3)
            for indicator in indicators["strong"]:
                if indicator in text_lower:
                    score += 3
                if indicator in filename_lower:
                    score += 2  # Filename match bonus
            
            # Medium indicators (weight: 2) 
            for indicator in indicators["medium"]:
                if indicator in text_lower:
                    score += 2
                if indicator in filename_lower:
                    score += 1
            
            # Weak indicators (weight: 1)
            for indicator in indicators["weak"]:
                if indicator in text_lower:
                    score += 1
            
            scores[category] = score
        
        # Additional context-based scoring
        lines = text.split('\n')
        
        # Look for structured patterns
        if any(line.strip().startswith(('1.', '2.', '3.', 'Step 1', 'Step 2')) for line in lines):
            scores["SOP_s"] += 2
        
        if any((':' in line and len(line.split(':')) == 2) for line in lines[:10]):
            if scores.get("Email_references", 0) > 0:
                scores["Email_references"] += 2
            if scores.get("Forms", 0) > 0:
                scores["Forms"] += 1
        
        # Return category with highest score
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        # Final fallback based on file content patterns
        if len(text) > 2000 and "step" in text_lower:
            return "SOP_s"
        elif "batch" in text_lower or "lot" in text_lower:
            return "Batch_records"
        elif len([line for line in lines if line.strip().endswith(':')]) > 3:
            return "Forms"
        
        return "Forms"  # Ultimate fallback

    @staticmethod
    def categorize_files_with_voice_titles(files_info: List[dict], user_audio: str = "") -> dict:
        """
        Emergency categorization that works without AI
        """
        file_mappings = []
        categories_found = []
        
        for idx, file_info in enumerate(files_info):
            filename = file_info.get("filename", "")
            text = file_info.get("text", "")
            
            # Classify the document
            category = EmergencyFileExtractService.classify_document_content(text, filename)
            categories_found.append(category)
            
            # Simple voice title matching
            voice_title = "User Title Not Specified"
            if user_audio and user_audio.strip():
                # Basic voice title extraction
                audio_words = user_audio.strip().split()
                if len(files_info) == 1:
                    voice_title = user_audio.strip()
                elif idx < len(audio_words):
                    voice_title = audio_words[idx] if audio_words else "User Title Not Specified"
            
            file_mappings.append({
                "filename": filename,
                "category": category,
                "voice_title": voice_title,
                "content_evidence": f"Rule-based classification based on content analysis"
            })
        
        # Generate overall title
        unique_categories = list(set(categories_found))
        if len(unique_categories) == 1:
            title_map = {
                "Batch_records": "Batch Production Documents",
                "SOP_s": "Standard Operating Procedures", 
                "Forms": "Form Collection",
                "Interviews": "Interview Records",
                "Logbooks": "Log Records",
                "Email_references": "Email Communications",
                "Certificates": "Certificate Collection"
            }
            overall_title = title_map.get(unique_categories[0], "Document Collection")
        else:
            overall_title = f"Mixed Document Collection ({len(files_info)} files)"
        
        return {
            "AI_suggested_Title": overall_title,
            "file_mappings": file_mappings
        }