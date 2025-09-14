#!/usr/bin/env python3
"""
Incident Service Module
Handles incident processing, transcription, and AI analysis
"""

import os
import tempfile
from typing import Optional, Tuple
from app.services.utils.transcription import VoiceTranscriber
from app.services.utils.ai_analysis import AIAnalyzer
from app.services.utils.document_ocr import DocumentOCR
from app.services.deviation.incident.incident_schema import IncidentSchema, IncidentAnalysis, IncidentResponse, IncidentSummaryResponse

class IncidentManager:
    """
    Main incident management class that orchestrates transcription and AI analysis
    """
    
    def __init__(self):
        """Initialize transcriber and analyzer"""
        self.transcriber = VoiceTranscriber()
        self.analyzer = AIAnalyzer()
        self.document_ocr = DocumentOCR()
        
    def process_incident_from_audio(self, audio_file_path: str) -> IncidentResponse:
        """
        Process incident from audio file - transcribe and analyze
        
        Args:
            audio_file_path (str): Path to audio file
            
        Returns:
            IncidentSchema: Complete incident processing response
        """
        try:
            # Step 1: Transcribe audio
            print("🎤 Starting audio transcription...")
            transcription = self.transcriber.transcribe_audio(audio_file_path)
            
            if not transcription:
                return IncidentResponse(
                    success=False,
                    message="Failed to transcribe audio file",
                    transcription=None,
                    incident_description=None,
                    headline=None,
                    analysis=None
                )
            
            print(f"✅ Transcription completed: {len(transcription)} characters")
            
            # Step 2: Process the transcribed text
            return self.process_incident_from_text(transcription)
            
        except Exception as e:
            print(f"❌ Error processing incident from audio: {str(e)}")
            return IncidentResponse(
                success=False,
                message=f"Error processing incident: {str(e)}",
                transcription=None,
                incident_description=None,
                headline=None,
                analysis=None
            )
    
    def process_incident_from_text(self, transcribed_text: str) -> IncidentResponse:
        """
        Process incident from transcribed text
        
        Args:
            transcribed_text (str): Transcribed text to analyze
            
        Returns:
            IncidentSchema: Complete incident processing response
        """
        try:
            # Step 1: Get incident description and headline
            print("🤖 Generating incident description...")
            incident_description, headline = self._generate_incident_description(transcribed_text)
            
            # Step 2: Get detailed analysis
            print("🔍 Performing detailed incident analysis...")
            analysis_data = self.analyzer.analyze_incident(transcribed_text)
            print("DEBUG: analysis_data type:", type(analysis_data))
            print("DEBUG: analysis_data value:", analysis_data)

            # Always attempt to return a structured response, even if analysis_data is missing or incomplete
            if not analysis_data or not isinstance(analysis_data, dict):
                print("WARNING: analysis_data is None, empty, or not a dict. Returning best-effort response.")
                analysis_data = {
                    'title': 'Not specified',
                    'who': 'Not specified',
                    'what': 'Not specified',
                    'where': 'Not specified',
                    'immediate_action': 'Not specified',
                    'quality_concerns': 'Not specified',
                    'quality_controls': 'Not specified',
                    'rca_tool': 'Not specified',
                    'expected_interim_action': 'Not specified',
                    'capa': 'Not specified',
                    'deviation_triage': None,
                    'product_quality': None,
                    'patient_safety': None,
                    'regulatory_impact': None,
                    'validation_impact': None,
                    'customer_notification': None,
                    'review_qta': None,
                    'criticality': None
                }
            # Step 3: Create structured analysis object
            try:
                analysis = IncidentAnalysis(
                    title=analysis_data.get('title', 'Not specified'),
                    who=analysis_data.get('who', 'Not specified'),
                    what=analysis_data.get('what', 'Not specified'),
                    where=analysis_data.get('where', 'Not specified'),
                    immediate_action=analysis_data.get('immediate_action', 'Not specified'),
                    quality_concerns=analysis_data.get('quality_concerns', 'Not specified'),
                    quality_controls=analysis_data.get('quality_controls', 'Not specified'),
                    rca_tool=analysis_data.get('rca_tool', 'Not specified'),
                    expected_interim_action=analysis_data.get('expected_interim_action', 'Not specified'),
                    capa=analysis_data.get('capa', 'Not specified')
                )
            except Exception as e:
                print("ERROR: Failed to create IncidentAnalysis:", e)
                analysis = None
            print("✅ Incident analysis completed (best effort)")
            result = IncidentResponse(
                success=True,
                message="Incident processed (best effort)",
                transcription=transcribed_text,
                incident_description=incident_description,
                headline=headline,
                analysis=analysis
            )
            # Attach new fields from analysis_data to the result object
            for field in [
                'deviation_triage', 'product_quality', 'patient_safety', 'regulatory_impact',
                'validation_impact', 'customer_notification', 'review_qta', 'criticality'
            ]:
                setattr(result, field, analysis_data.get(field))
            print("DEBUG: IncidentResponse result:", result)
            return result
            
        except Exception as e:
            print(f"❌ Error processing incident from text: {str(e)}")
            return IncidentResponse(
                success=False,
                message=f"Error processing incident: {str(e)}",
                transcription=transcribed_text,
                incident_description=None,
                headline=None,
                analysis=None
            )
    
    def _generate_incident_description(self, transcribed_text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate incident description and headline
        
        Args:
            transcribed_text (str): Transcribed text
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (incident_description, headline)
        """
        try:
            # Use AI analyzer to get summary and generate headline
            summary = self.analyzer.get_summary_analysis(transcribed_text)
            
            if not summary:
                return None, None
            
            # Generate headline from summary
            headline = self._generate_headline(summary)
            
            return summary, headline
            
        except Exception as e:
            print(f"❌ Error generating incident description: {str(e)}")
            return None, None
    
    def _generate_headline(self, incident_description: str) -> Optional[str]:
        """
        Generate a succinct headline from incident description
        
        Args:
            incident_description (str): Full incident description
            
        Returns:
            Optional[str]: Succinct headline
        """
        try:
            # Use AI to generate a headline
            prompt = f"""
Create a succinct, professional headline (maximum 10 words) for this incident:

"{incident_description}"

The headline should be:
- Clear and specific
- Professional tone
- Maximum 10 words
- Capture the essence of the incident

Provide ONLY the headline, no additional text.
"""
            
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.analyzer.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 50,
                'temperature': 0.3
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                headline = result['choices'][0]['message']['content'].strip()
                # Remove quotes if present
                headline = headline.strip('"\'')
                return headline
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error generating headline: {str(e)}")
            return None
    
    def get_incident_summary(self, transcribed_text: str) -> IncidentSummaryResponse:
        """
        Get a quick summary of the incident
        
        Args:
            transcribed_text (str): Transcribed text
            
        Returns:
            IncidentSchema: Summary response
        """
        try:
            summary = self.analyzer.get_summary_analysis(transcribed_text)
            headline = self._generate_headline(summary) if summary else None
            
            if summary:
                return IncidentSummaryResponse(
                    success=True,
                    message="Summary generated successfully",
                    summary=summary,
                    headline=headline
                )
            else:
                return IncidentSummaryResponse(
                    success=False,
                    message="Failed to generate summary",
                    summary=None,
                    headline=None
                )
                
        except Exception as e:
            print(f"❌ Error getting incident summary: {str(e)}")
            return IncidentSummaryResponse(
                success=False,
                message=f"Error generating summary: {str(e)}",
                summary=None,
                headline=None
            )
    
    def validate_audio_file(self, file_path: str) -> bool:
        """
        Validate audio file before processing
        
        Args:
            file_path (str): Path to audio file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                print(f"❌ Audio file not found: {file_path}")
                return False
            
            # Check file size (25MB limit for Whisper)
            file_size = os.path.getsize(file_path)
            if file_size > 25 * 1024 * 1024:
                print(f"❌ File too large: {file_size} bytes (max 25MB)")
                return False
            
            # Check file extension
            valid_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4']
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension not in valid_extensions:
                print(f"❌ Unsupported file format: {file_extension}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating audio file: {str(e)}")
            return False
    
    def process_uploaded_file(self, file_content: bytes, filename: str) -> IncidentResponse:
        """
        Process uploaded file content
        
        Args:
            file_content (bytes): File content
            filename (str): Original filename
            
        Returns:
            IncidentSchema: Processing response
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Process the temporary file
                result = self.process_incident_from_audio(tmp_file_path)
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            print(f"❌ Error processing uploaded file: {str(e)}")
            return IncidentResponse(
                success=False,
                message=f"Error processing uploaded file: {str(e)}",
                transcription=None,
                incident_description=None,
                headline=None,
                analysis=None
            )
    
    def display_incident_results(self, response: IncidentResponse):
        """
        Display incident results in a formatted way
        
        Args:
            response (IncidentSchema): Incident response to display
        """
        print("\n" + "="*50)
        print("INCIDENT ANALYSIS RESULTS")
        print("="*50)
        
        if not response.success:
            print(f"❌ Error: {response.message}")
            return
        
        # Display headline
        if response.headline:
            print(f"\n📌 HEADLINE: {response.headline}")
        
        # Display incident description
        if response.incident_description:
            print(f"\n📝 INCIDENT DESCRIPTION:")
            print(f"{response.incident_description}")
        
        # Display detailed analysis
        if response.analysis:
            print(f"\n🔍 DETAILED ANALYSIS:")
            print(f"Title: {response.analysis.title}")
            print(f"Who: {response.analysis.who}")
            print(f"What: {response.analysis.what}")
            print(f"Where: {response.analysis.where}")
            print(f"Immediate Action: {response.analysis.immediate_action}")
            print(f"Quality Concerns: {response.analysis.quality_concerns}")
            print(f"Quality Controls: {response.analysis.quality_controls}")
            print(f"RCA Tool: {response.analysis.rca_tool}")
            print(f"Expected Interim Action: {response.analysis.expected_interim_action}")
            print(f"CAPA: {response.analysis.capa}")
        
        # Display transcription
        if response.transcription:
            print(f"\n🎤 ORIGINAL TRANSCRIPTION:")
            print(f"{response.transcription}")
        
        print(f"\n⏰ Processed at: {response.timestamp}")
        print("="*50)

    def process_uploaded_document(self, file_content: bytes, filename: str) -> IncidentResponse:
        """
        Process uploaded document file (PDF, DOCX, TXT) and analyze incident
        Args:
            file_content (bytes): File content
            filename (str): Original filename
        Returns:
            IncidentResponse: Processing response
        """
        import os
        import tempfile
        extracted_text = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            try:
                # Use DocumentOCR for all document extraction
                extracted_text = self.document_ocr.process_file(tmp_file_path)
                if not extracted_text or not extracted_text.strip():
                    return IncidentResponse(
                        success=False,
                        message="No text could be extracted from the document.",
                        transcription=None,
                        incident_description=None,
                        headline=None,
                        analysis=None
                    )
                # --- Robust Preprocessing for Extracted Text ---
                def clean_text(text):
                    import re
                    # Remove repeated headers/footers (lines repeated more than 3 times)
                    lines = text.splitlines()
                    from collections import Counter
                    line_counts = Counter(lines)
                    cleaned_lines = [line for line in lines if line_counts[line] <= 3]
                    # Remove empty lines and lines with only special characters
                    cleaned_lines = [line for line in cleaned_lines if line.strip() and re.search(r'[A-Za-z0-9]', line)]
                    cleaned = "\n".join(cleaned_lines)
                    # Remove excessive whitespace
                    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
                    return cleaned.strip()

                cleaned_text = clean_text(extracted_text)
                # Truncate to 4000 characters for AI prompt
                max_len = 4000
                truncated_text = cleaned_text[:max_len]

                # Add context if the document looks like a form/table
                if any(keyword in truncated_text.lower() for keyword in ["form", "table", "date", "signature", "approved by", "reviewed by", "agreement", "contract", "qta"]):
                    context_prompt = (
                        "This document appears to be a form, table, or contract/agreement. "
                        "If it is a contract or agreement (such as a Quality Technical Agreement), extract and summarize: "
                        "- The parties involved\n- Effective dates\n- Main responsibilities\n- Any sections related to deviations, incidents, or quality\n" 
                        "If it is a form or table, extract and summarize any incident, deviation, or key information relevant to pharmaceutical quality, compliance, or investigation. "
                        "If the document is a blank form, state that no incident information is present.\n\n"
                    )
                    ai_input = context_prompt + truncated_text
                else:
                    ai_input = truncated_text

                # Debug: Log and return extracted text if analysis fails
                analysis_result = self.process_incident_from_text(ai_input)
                if not analysis_result.success:
                    return IncidentResponse(
                        success=False,
                        message="Failed to analyze incident. Extracted/cleaned text was: " + (ai_input[:500] + ("..." if len(ai_input) > 500 else "")),
                        transcription=ai_input,
                        incident_description=None,
                        headline=None,
                        analysis=None
                    )
                return analysis_result
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
        except Exception as e:
            return IncidentResponse(
                success=False,
                message=f"Error processing uploaded document: {str(e)}",
                transcription=None,
                incident_description=None,
                headline=None,
                analysis=None
            )