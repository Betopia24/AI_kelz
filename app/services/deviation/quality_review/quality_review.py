#!/usr/bin/env python3
"""
Quality Review Module
Handles voice transcription, AI analysis for quality and SME reviews, 
and document processing with summarization
"""

import os
import sys
import tempfile
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

# Add the app directory to Python path for imports
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, app_dir)

from app.services.utils.transcription import VoiceTranscriber
from app.services.utils.ai_analysis import AIAnalyzer
from app.services.utils.document_ocr import DocumentOCR


class QualityReviewer:
    """
    Quality Review component that handles voice transcription, 
    AI analysis, and document processing
    """
    
    def __init__(self):
        """Initialize all required services"""
        self.transcriber = VoiceTranscriber()
        self.ai_analyzer = AIAnalyzer()
        self.document_ocr = DocumentOCR()
        


    def process_voice_for_quality_review(self, audio_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Process voice file for quality review analysis
        
        Args:
            audio_file_path (str): Path to audio file
            
        Returns:
            Dict containing transcription and quality/SME review analysis
        """
        try:
            # Step 1: Transcribe the audio
            original_transcription, polished_transcription = self.transcriber.process_file_with_results(audio_file_path)
            if not original_transcription:
                return None
            # Step 2: Perform Quality Review Analysis
            quality_review_result = self._perform_quality_review_analysis(original_transcription)
            # Step 3: Perform SME Review Analysis
            sme_review_result = self._perform_sme_review_analysis(original_transcription)
            return {
                "status": "success",
                "transcription": {
                    "original": original_transcription,
                    "polished": polished_transcription,
                    "length": len(original_transcription)
                },
                "quality_review": quality_review_result,
                "sme_review": sme_review_result,
                "message": "Voice quality review completed successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Voice quality review failed"
            }

    def _perform_quality_review_analysis(self, transcribed_text: str) -> Optional[Dict[str, Any]]:
        """
        Perform quality review analysis using AI
        
        Args:
            transcribed_text (str): Transcribed text to analyze
            
        Returns:
            Dict containing quality review analysis
        """
        try:
            quality_prompt = f"""
You are an expert Quality Assurance reviewer in a pharmaceutical environment. Analyze the following transcribed investigation content and provide a comprehensive Quality Review assessment.

Please evaluate and provide your analysis in this EXACT format:

===QUALITY REVIEW START===
OVERALL_ASSESSMENT: [Satisfactory/Needs Improvement/Unsatisfactory - with brief justification]

INVESTIGATION_COMPLETENESS:
Investigation Status: [Complete/Incomplete/Partially Complete]
Completeness Score: [1-10 scale]
Missing Elements: [List any missing investigation elements]
Adequacy Assessment: [Detailed assessment of investigation thoroughness]

ROOT_CAUSE_ANALYSIS:
Root Cause Identified: [Yes/No/Partially]
Root Cause Quality: [Adequate/Inadequate/Needs Enhancement]
Analysis Method Used: [Identify the RCA method if mentioned]
Depth of Analysis: [Shallow/Moderate/Comprehensive]
Root Cause Statement: [Extract or summarize the root cause if provided]

CAPA_ASSESSMENT:
CAPA Actions Identified: [Yes/No/Partially]
CAPA Adequacy: [Adequate/Inadequate/Needs Enhancement]
Prevention Focus: [Strong/Moderate/Weak]
Corrective Actions: [List corrective actions mentioned]
Preventive Actions: [List preventive actions mentioned]
CAPA Effectiveness Potential: [High/Medium/Low]

RISK_EVALUATION:
Risks Discussed: [Yes/No/Partially]
Risk Assessment Quality: [Comprehensive/Moderate/Limited]
Risk Mitigation: [Adequate/Inadequate/Not Addressed]
Identified Risks: [List risks mentioned in investigation]
Mitigation Strategies: [List mitigation strategies discussed]

QUALITY_CONCERNS:
Product Impact: [Assessed/Not Assessed/Unclear]
Patient Safety: [Considered/Not Considered/Unclear]
Regulatory Compliance: [Addressed/Not Addressed/Unclear]
Quality System Impact: [Evaluated/Not Evaluated/Unclear]

RECOMMENDATIONS:
Quality Reviewer Actions: [List specific actions needed]
Follow-up Required: [List follow-up activities needed]
Additional Investigation: [Yes/No - with details if yes]
Documentation Requirements: [List additional documentation needed]
===QUALITY REVIEW END===

TRANSCRIBED INVESTIGATION CONTENT:
"{transcribed_text}"

INSTRUCTIONS:
- Be specific and provide detailed assessments
- Use pharmaceutical industry standards and GMP requirements
- If information is missing, specifically note what is lacking
- Provide actionable recommendations
- Focus on compliance and patient safety implications
"""
            
            quality_analysis = self.ai_analyzer.analyze_with_prompt(quality_prompt)
            if quality_analysis:
                return self._parse_quality_review_response(quality_analysis)
            else:
                return None
        except Exception as e:
            return None

    def _perform_sme_review_analysis(self, transcribed_text: str) -> Optional[Dict[str, Any]]:
        """
        Perform SME (Subject Matter Expert) review analysis using AI
        
        Args:
            transcribed_text (str): Transcribed text to analyze
            
        Returns:
            Dict containing SME review analysis
        """
        try:
            sme_prompt = f"""
You are a Subject Matter Expert (SME) reviewer with deep technical expertise in pharmaceutical operations, manufacturing, and quality systems. Analyze the following transcribed investigation content and provide a comprehensive SME Review assessment.

Please evaluate and provide your analysis in this EXACT format:

===SME REVIEW START===
SME_OVERALL_ASSESSMENT: [Satisfactory/Needs Improvement/Unsatisfactory - with technical justification]

TECHNICAL_INVESTIGATION_REVIEW:
Investigation Methodology: [Appropriate/Inappropriate/Needs Enhancement]
Technical Depth: [Comprehensive/Moderate/Insufficient]
Scientific Approach: [Sound/Questionable/Flawed]
Data Analysis Quality: [Thorough/Adequate/Inadequate]
Investigation Scope: [Complete/Incomplete/Needs Expansion]

TECHNICAL_ROOT_CAUSE_ASSESSMENT:
Root Cause Technical Validity: [Valid/Questionable/Invalid]
Technical Evidence Supporting RCA: [Strong/Moderate/Weak]
Scientific Method Application: [Proper/Improper/Unclear]
Technical Analysis Tools Used: [List tools/methods identified]
Alternative Causes Considered: [Yes/No/Partially]

TECHNICAL_CAPA_EVALUATION:
Technical Feasibility: [High/Medium/Low]
Implementation Complexity: [Simple/Moderate/Complex]
Technical Resource Requirements: [Identified/Not Identified/Unclear]
Technology/Process Changes: [Appropriate/Inappropriate/Unclear]
Technical Risk of CAPA Implementation: [Low/Medium/High]

PROCESS_AND_SYSTEM_ANALYSIS:
Process Understanding: [Demonstrated/Limited/Not Demonstrated]
System Knowledge: [Comprehensive/Adequate/Inadequate]
Equipment Considerations: [Addressed/Not Addressed/Unclear]
Technology Factors: [Considered/Not Considered/Unclear]
Process Interaction Effects: [Evaluated/Not Evaluated/Unclear]

TECHNICAL_RISK_ASSESSMENT:
Technical Risk Identification: [Comprehensive/Partial/Inadequate]
Process Risk Evaluation: [Thorough/Moderate/Limited]
System Risk Analysis: [Complete/Incomplete/Not Performed]
Technical Risk Mitigation: [Effective/Moderate/Ineffective]
Cross-functional Impact: [Assessed/Not Assessed/Unclear]

SME_TECHNICAL_RECOMMENDATIONS:
Technical Improvements Needed: [List specific technical recommendations]
Additional Technical Investigation: [Required/Not Required/Conditional]
Expert Consultation Needed: [Yes/No - specify areas if yes]
Technical Validation Required: [List validation activities needed]
Process/System Modifications: [List recommended modifications]
===SME REVIEW END===

TRANSCRIBED INVESTIGATION CONTENT:
"{transcribed_text}"

INSTRUCTIONS:
- Apply deep technical expertise and industry best practices
- Focus on technical accuracy and scientific validity
- Identify technical gaps and provide expert recommendations
- Consider cross-functional technical impacts
- Evaluate technical feasibility of proposed solutions
- If technical information is insufficient, specify what additional data is needed
"""
            
            sme_analysis = self.ai_analyzer.analyze_with_prompt(sme_prompt)
            if sme_analysis:
                return self._parse_sme_review_response(sme_analysis)
            else:
                return None
        except Exception as e:
            return None

    def _parse_quality_review_response(self, analysis_text: str) -> Dict[str, Any]:
        """Parse the quality review AI response"""
        try:
            import re
            quality_data = {
                "overall_assessment": "",
                "investigation_completeness": {},
                "root_cause_analysis": {},
                "capa_assessment": {},
                "risk_evaluation": {},
                "quality_concerns": {},
                "recommendations": {}
            }
            
            # Extract content between markers
            start_marker = "===QUALITY REVIEW START==="
            end_marker = "===QUALITY REVIEW END==="
            
            if start_marker in analysis_text and end_marker in analysis_text:
                content = analysis_text.split(start_marker)[1].split(end_marker)[0]
            else:
                content = analysis_text
            
            # Parse main sections
            sections = {
                "overall_assessment": r'OVERALL_ASSESSMENT:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "investigation_completeness": r'INVESTIGATION_COMPLETENESS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "root_cause_analysis": r'ROOT_CAUSE_ANALYSIS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "capa_assessment": r'CAPA_ASSESSMENT:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "risk_evaluation": r'RISK_EVALUATION:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "quality_concerns": r'QUALITY_CONCERNS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "recommendations": r'RECOMMENDATIONS:\s*(.+?)(?=\n[A-Z_]+:|$)'
            }
            
            for key, pattern in sections.items():
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    section_content = match.group(1).strip()
                    if key == "overall_assessment":
                        quality_data[key] = section_content
                    else:
                        # Parse subsections for complex sections
                        quality_data[key] = self._parse_section_content(section_content)
            
            return quality_data
        except Exception as e:
            return {"error": "Failed to parse quality review response", "raw_response": analysis_text}

    def _parse_sme_review_response(self, analysis_text: str) -> Dict[str, Any]:
        """Parse the SME review AI response"""
        try:
            import re
            sme_data = {
                "sme_overall_assessment": "",
                "technical_investigation_review": {},
                "technical_root_cause_assessment": {},
                "technical_capa_evaluation": {},
                "process_and_system_analysis": {},
                "technical_risk_assessment": {},
                "sme_technical_recommendations": {}
            }
            
            # Extract content between markers
            start_marker = "===SME REVIEW START==="
            end_marker = "===SME REVIEW END==="
            
            if start_marker in analysis_text and end_marker in analysis_text:
                content = analysis_text.split(start_marker)[1].split(end_marker)[0]
            else:
                content = analysis_text
            
            # Parse main sections
            sections = {
                "sme_overall_assessment": r'SME_OVERALL_ASSESSMENT:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "technical_investigation_review": r'TECHNICAL_INVESTIGATION_REVIEW:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "technical_root_cause_assessment": r'TECHNICAL_ROOT_CAUSE_ASSESSMENT:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "technical_capa_evaluation": r'TECHNICAL_CAPA_EVALUATION:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "process_and_system_analysis": r'PROCESS_AND_SYSTEM_ANALYSIS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "technical_risk_assessment": r'TECHNICAL_RISK_ASSESSMENT:\s*(.+?)(?=\n[A-Z_]+:|$)',
                "sme_technical_recommendations": r'SME_TECHNICAL_RECOMMENDATIONS:\s*(.+?)(?=\n[A-Z_]+:|$)'
            }
            
            for key, pattern in sections.items():
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    section_content = match.group(1).strip()
                    if key == "sme_overall_assessment":
                        sme_data[key] = section_content
                    else:
                        # Parse subsections for complex sections
                        sme_data[key] = self._parse_section_content(section_content)
            
            return sme_data
        except Exception as e:
            return {"error": "Failed to parse SME review response", "raw_response": analysis_text}

    def _parse_section_content(self, section_content: str) -> Dict[str, str]:
        """Parse section content into key-value pairs"""
        try:
            import re
            
            result = {}
            lines = section_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    result[key] = value
            
            return result
            
        except Exception as e:
            return {"content": section_content}

    def process_document_for_summary(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Process document file and create AI summary
        
        Args:
            file_path (str): Path to document file
            
        Returns:
            Dict containing extracted text and AI summary
        """
        try:
            # Step 1: Extract text using OCR
            extracted_text = self.document_ocr.extract_text(file_path)
            if not extracted_text or not extracted_text.strip():
                return {
                    "status": "warning",
                    "extracted_text": "",
                    "summary": "",
                    "message": "No text could be extracted from the document"
                }
            # Step 2: Generate AI summary
            summary = self._generate_document_summary(extracted_text)
            return {
                "status": "success",
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "summary": summary,
                "message": "Document processing and summarization completed successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Document processing failed"
            }

    def _generate_document_summary(self, extracted_text: str) -> Optional[str]:
        """
        Generate AI summary of extracted document text
        
        Args:
            extracted_text (str): Text extracted from document
            
        Returns:
            String containing AI-generated summary
        """
        try:
            summary_prompt = f"""
You are an expert document analyzer specializing in pharmaceutical and quality documentation. Please analyze the following extracted document text and provide a comprehensive summary.

Please provide your summary in this structured format:

===DOCUMENT SUMMARY START===
DOCUMENT_TYPE: [Identify the type of document - SOP, Investigation Report, Deviation Report, CAPA, etc.]

EXECUTIVE_SUMMARY: [2-3 sentence high-level summary of the document]

KEY_FINDINGS:
• [List main findings, conclusions, or key points from the document]
• [Continue with additional key findings]

MAIN_SECTIONS:
• [List the main sections or topics covered in the document]
• [Continue with additional sections]

IMPORTANT_DETAILS:
• [Extract important dates, numbers, names, or specific details]
• [Continue with additional important details]

ACTION_ITEMS: [List any action items, recommendations, or next steps mentioned]

QUALITY_RELEVANCE: [Explain the relevance to quality systems, compliance, or pharmaceutical operations]

REGULATORY_IMPLICATIONS: [Note any regulatory or compliance implications if mentioned]
===DOCUMENT SUMMARY END===

EXTRACTED DOCUMENT TEXT:
"{extracted_text}"

INSTRUCTIONS:
- Provide a clear, concise, and comprehensive summary
- Focus on key information that would be important for quality review
- Identify any quality, compliance, or regulatory aspects
- If the document is unclear or incomplete, note this in your summary
- Extract specific details like dates, numbers, and names when relevant
"""
            
            summary = self.ai_analyzer.analyze_with_prompt(summary_prompt)
            if summary:
                return summary
            else:
                return "Summary generation failed"
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def process_combined_review(self, audio_file_path: str, document_file_path: str) -> Dict[str, Any]:
        """
        Process both voice and document for complete quality review
        
        Args:
            audio_file_path (str): Path to audio file
            document_file_path (str): Path to document file
            
        Returns:
            Dict containing combined review results
        """
        try:
            # Process voice
            voice_result = self.process_voice_for_quality_review(audio_file_path)
            # Process document
            document_result = self.process_document_for_summary(document_file_path)
            return {
                "status": "success",
                "voice_analysis": voice_result,
                "document_analysis": document_result,
                "message": "Combined quality review completed successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Combined quality review failed"
            }


# Standalone functions for direct usage
def process_voice_quality_review(audio_file_path: str) -> Optional[Dict[str, Any]]:
    """
    Standalone function to process voice for quality review
    
    Args:
        audio_file_path (str): Path to audio file
        
    Returns:
        Dict containing quality review results
    """
    try:
        reviewer = QualityReviewer()
        return reviewer.process_voice_for_quality_review(audio_file_path)
    except Exception as e:
        return None

def process_document_summary(document_file_path: str) -> Optional[Dict[str, Any]]:
    """
    Standalone function to process document for summary
    
    Args:
        document_file_path (str): Path to document file
        
    Returns:
        Dict containing document summary results
    """
    try:
        reviewer = QualityReviewer()
        return reviewer.process_document_for_summary(document_file_path)
    except Exception as e:
        return None