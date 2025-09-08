#!/usr/bin/env python3
"""
Improved AI Analysis Module
Enhanced incident analysis specifically designed for pharmaceutical deviation workflow
"""

import requests
import json
import re
import os
import sys
from typing import Dict, Any, Optional

# Add the app directory to Python path for imports
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, app_dir)

from app.config.config import OPENAI_API_KEY

class AIAnalyzer:
    def __init__(self):
        # Load configuration from environment
        self.openai_api_key = OPENAI_API_KEY
        
        # Validate API key
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    def analyze_with_prompt(self, prompt: str) -> str:
        """
        Analyze content with a custom prompt and return the AI's response as a string.
        Enhanced with better error handling and debugging.
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'system',
                        'content': '''You are an expert pharmaceutical deviation investigator with extensive experience in GMP compliance, quality systems, and regulatory requirements. 

Key principles:
- Focus primarily on audio content for incident details (who, what, where)
- Use document content to supplement and provide background context
- Always provide actionable, pharmaceutical industry-specific recommendations
- Follow structured analysis format exactly as requested
- Make intelligent assessments for impact categories even when not explicitly mentioned'''
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 4000,
                'temperature': 0.3,
                'top_p': 0.9
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            
            print("DEBUG: OpenAI API Response Status:", response.status_code)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                if ai_response and len(ai_response) >= 100:
                    return ai_response
                return None
            elif response.status_code == 429:
                print("DEBUG: Rate limit exceeded")
                return None
            elif response.status_code == 401:
                print("DEBUG: Authentication failed")
                return None
            else:
                print(f"DEBUG: API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("DEBUG: Request timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("DEBUG: Connection error")
            return None
        except Exception as e:
            print(f"DEBUG: Unexpected error: {str(e)}")
            return None

    def analyze_incident(self, combined_text: str) -> Optional[Dict[str, Any]]:
        """
        Main incident analysis method following your specific workflow requirements
        """
        try:
            print("DEBUG: Starting incident analysis...")
            
            # Truncate input if too long to avoid context overflow
            max_len = 8000
            if len(combined_text) > max_len:
                truncated_text = combined_text[:max_len] + "\n[...TEXT TRUNCATED...]"
                print(f"DEBUG: Text truncated from {len(combined_text)} to {len(truncated_text)} characters")
            else:
                truncated_text = combined_text
            
            structured_data = self._get_enhanced_structured_analysis(truncated_text)
            
            if structured_data and self._validate_analysis_result(structured_data):
                print("DEBUG: Analysis completed successfully")
                return structured_data
            else:
                print("DEBUG: Analysis failed validation")
                return None
                
        except Exception as e:
            print(f"DEBUG: Error in analyze_incident: {str(e)}")
            return None

    def _get_enhanced_structured_analysis(self, text_content: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced structured analysis with improved prompting for pharmaceutical incidents
        """
        try:
            prompt = f"""
PHARMACEUTICAL INCIDENT ANALYSIS

You are analyzing content from multiple sources for a pharmaceutical deviation investigation. 
The content may include:
- Audio transcriptions (primary source for incident details)
- Document content (supporting background information)

CRITICAL INSTRUCTIONS:
1. Focus PRIMARY on audio transcriptions for WHO, WHAT, WHERE details
2. Use document content to SUPPLEMENT and provide additional context
3. For impact assessments, use your pharmaceutical expertise to make intelligent evaluations
4. ALWAYS fill every field - never leave blank or "Not specified"
5. Follow the EXACT format below

RESPONSE FORMAT (respond ONLY in this format):

===ANALYSIS START===
INCIDENT_TITLE: [Generate a clear, specific title based on the incident]
WHO: [People involved - primarily from audio, supplemented by documents]
WHAT: [What happened - detailed description from all sources]
WHERE: [Location/department/area - from audio primarily]
IMMEDIATE_ACTION: [Actions taken immediately - from content or your recommendations]
QUALITY_CONCERNS: [Quality issues identified or potential impacts]
QUALITY_CONTROLS: [Controls that failed or need implementation]
RCA_TOOL: [Recommended root cause analysis method]
EXPECTED_INTERIM_ACTION: [Interim measures to prevent recurrence]
CAPA: [Corrective and Preventive Actions recommended]

DEVIATION_TRIAGE: Yes
PRODUCT_QUALITY: {{"yes_no": "Yes/No", "level": "High/Medium/Low or null"}}
PATIENT_SAFETY: {{"yes_no": "Yes/No", "level": "High/Medium/Low or null"}}
REGULATORY_IMPACT: {{"yes_no": "Yes/No", "level": "High/Medium/Low or null"}}
VALIDATION_IMPACT: Yes/No
CUSTOMER_NOTIFICATION: Yes/No
REVIEW_QTA: [Summary about quality technical agreements]
CRITICALITY: Critical/Major/Minor
===ANALYSIS END===

CONTENT TO ANALYZE:
{text_content}

Analyze the above content and provide your structured response:"""

            print("DEBUG: Sending enhanced prompt to OpenAI...")
            
            analysis_text = self.analyze_with_prompt(prompt)
            
            if not analysis_text:
                print("DEBUG: No response from OpenAI")
                return None
                
            print("DEBUG: Received response from OpenAI, parsing...")
            
            # Parse the structured response
            incident_data = self._parse_structured_response(analysis_text)
            
            if incident_data:
                print("DEBUG: Successfully parsed incident data")
                return incident_data
            else:
                print("DEBUG: Failed to parse incident data")
                return None
                
        except Exception as e:
            print(f"DEBUG: Error in _get_enhanced_structured_analysis: {str(e)}")
            return None

    def _parse_structured_response(self, analysis_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the structured AI response into a dictionary
        """
        try:
            # Initialize the result dictionary
            incident_data = {
                'title': '',
                'who': '',
                'what': '',
                'where': '',
                'immediate_action': '',
                'quality_concerns': '',
                'quality_controls': '',
                'rca_tool': '',
                'expected_interim_action': '',
                'capa': '',
                'deviation_triage': 'Yes',
                'product_quality': {'yes_no': 'No', 'level': None},
                'patient_safety': {'yes_no': 'No', 'level': None},
                'regulatory_impact': {'yes_no': 'No', 'level': None},
                'validation_impact': 'No',
                'customer_notification': 'No',
                'review_qta': '',
                'criticality': 'Minor'
            }
            
            # Extract content between markers if present
            start_marker = "===ANALYSIS START==="
            end_marker = "===ANALYSIS END==="
            
            if start_marker in analysis_text and end_marker in analysis_text:
                content = analysis_text.split(start_marker)[1].split(end_marker)[0]
            else:
                content = analysis_text
            
            # Define regex patterns for extraction
            patterns = {
                'title': r'INCIDENT_TITLE:\s*(.+?)(?=\n\w+:|$)',
                'who': r'WHO:\s*(.+?)(?=\n\w+:|$)',
                'what': r'WHAT:\s*(.+?)(?=\n\w+:|$)',
                'where': r'WHERE:\s*(.+?)(?=\n\w+:|$)',
                'immediate_action': r'IMMEDIATE_ACTION:\s*(.+?)(?=\n\w+:|$)',
                'quality_concerns': r'QUALITY_CONCERNS:\s*(.+?)(?=\n\w+:|$)',
                'quality_controls': r'QUALITY_CONTROLS:\s*(.+?)(?=\n\w+:|$)',
                'rca_tool': r'RCA_TOOL:\s*(.+?)(?=\n\w+:|$)',
                'expected_interim_action': r'EXPECTED_INTERIM_ACTION:\s*(.+?)(?=\n\w+:|$)',
                'capa': r'CAPA:\s*(.+?)(?=\n\w+:|$)',
                'deviation_triage': r'DEVIATION_TRIAGE:\s*(.+?)(?=\n\w+:|$)',
                'product_quality': r'PRODUCT_QUALITY:\s*(\{.*?\})',
                'patient_safety': r'PATIENT_SAFETY:\s*(\{.*?\})',
                'regulatory_impact': r'REGULATORY_IMPACT:\s*(\{.*?\})',
                'validation_impact': r'VALIDATION_IMPACT:\s*(.+?)(?=\n\w+:|$)',
                'customer_notification': r'CUSTOMER_NOTIFICATION:\s*(.+?)(?=\n\w+:|$)',
                'review_qta': r'REVIEW_QTA:\s*(.+?)(?=\n\w+:|$)',
                'criticality': r'CRITICALITY:\s*(.+?)(?=\n\w+:|$)'
            }
            
            # Extract each field
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean up whitespace and newlines
                    value = re.sub(r'\n\s*', ' ', value).strip()
                    
                    # Special handling for JSON fields
                    if key in ['product_quality', 'patient_safety', 'regulatory_impact']:
                        try:
                            # Parse JSON
                            json_value = json.loads(value)
                            incident_data[key] = json_value
                        except (json.JSONDecodeError, ValueError):
                            # Fallback for malformed JSON
                            print(f"DEBUG: Failed to parse JSON for {key}: {value}")
                            incident_data[key] = {'yes_no': 'Yes', 'level': 'Medium'}
                    else:
                        incident_data[key] = value if value else incident_data[key]
            
            return incident_data
            
        except Exception as e:
            print(f"DEBUG: Error parsing structured response: {str(e)}")
            return None

    def _validate_analysis_result(self, incident_data: Dict[str, Any]) -> bool:
        """
        Validate that the analysis contains meaningful information
        """
        if not incident_data:
            return False
        
        # Check that key fields have meaningful content
        title = incident_data.get('title', '').strip()
        what = incident_data.get('what', '').strip()
        
        if not title or len(title) < 5:
            print("DEBUG: Title validation failed")
            return False
            
        if not what or len(what) < 10:
            print("DEBUG: What validation failed")
            return False
        
        # Validate JSON structure for impact fields
        for field in ['product_quality', 'patient_safety', 'regulatory_impact']:
            field_data = incident_data.get(field, {})
            if not isinstance(field_data, dict) or 'yes_no' not in field_data:
                print(f"DEBUG: {field} validation failed")
                return False
        
        return True

    def analyze(self, text_content: str) -> Dict[str, Any]:
        """
        Legacy method name for backwards compatibility
        """
        result = self.analyze_incident(text_content)
        if result:
            return {
                'success': True,
                'message': 'Analysis completed successfully',
                **result
            }
        else:
            return {
                'success': False,
                'message': 'Analysis failed',
                'incident_title': 'Analysis Failed',
                'who': 'Unknown',
                'what': 'Analysis could not be completed',
                'where': 'Unknown',
                'immediate_action': 'Manual review required',
                'quality_concerns': 'System analysis failure',
                'quality_controls': 'Manual validation needed',
                'rca_tool': 'Manual investigation',
                'expected_interim_action': 'Escalate for manual review',
                'capa': 'System improvement required'
            }

    def get_summary_analysis(self, transcribed_text: str) -> Optional[str]:
        """
        Get a quick summary analysis of the incident
        """
        try:
            prompt = f"""
Provide a brief 2-3 sentence summary of this pharmaceutical incident or event:

"{transcribed_text}"

Focus on: what happened, who was involved, and the key concern from a pharmaceutical/GMP perspective.
"""
            return self.analyze_with_prompt(prompt)
        except Exception as e:
            print(f"DEBUG: Error in get_summary_analysis: {str(e)}")
            return None

    def analyze_investigation_context(self, context: str) -> Dict[str, Any]:
        """
        Specialized method for investigation context analysis
        """
        investigation_prompt = f"""
        Analyze the following pharmaceutical deviation investigation context and provide comprehensive insights:
        
        {context}
        
        Please provide analysis covering:
        1. Background summary
        2. Timeline and affected systems
        3. Root cause analysis
        4. Impact assessment
        5. Corrective and preventive action recommendations
        6. Risk evaluation and compliance implications
        
        Format the response as a structured JSON analysis suitable for pharmaceutical deviation investigations.
        
        Use this structure:
        {{
            "background_summary": "Investigation analysis based on provided context and deviation data",
            "discussion": {{
                "timeline": "Event timeline constructed from available information",
                "affected_systems": ["Systems identified from context analysis"],
                "initial_findings": "Preliminary findings based on incident description and background"
            }},
            "root_cause_analysis": {{
                "primary_cause": "Root cause identified through systematic analysis",
                "contributing_factors": ["Contributing factors derived from context"],
                "methodology": "Structured root cause analysis methodology applied",
                "evidence": ["Evidence gathered from provided documentation"]
            }},
            "final_assessment": {{
                "impact_analysis": "Comprehensive impact assessment based on triage data",
                "risk_evaluation": "Risk evaluation considering all factors",
                "compliance_implications": "Regulatory and compliance considerations",
                "recurrence_probability": "Likelihood assessment of similar incidents"
            }},
            "capa_recommendations": {{
                "immediate_actions": ["Immediate corrective actions recommended"],
                "long_term_actions": ["Long-term preventive measures suggested"],
                "responsible_parties": ["Recommended responsible parties"],
                "timeline": "Suggested implementation timeline"
            }},
            "ai_generated_insights": {{
                "pattern_analysis": "Analysis of patterns and trends",
                "risk_mitigation": "Additional risk mitigation strategies",
                "process_improvements": ["Process improvement recommendations"],
                "monitoring_recommendations": ["Ongoing monitoring suggestions"]
            }}
        }}
        """
        try:
            response = self.analyze_with_prompt(investigation_prompt)
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return {
                        "analysis": response,
                        "status": "text_response",
                        "requires_manual_parsing": True
                    }
            else:
                return {
                    "analysis": "Investigation analysis failed - no response received",
                    "status": "error"
                }
        except Exception as e:
            return {
                "analysis": f"Investigation analysis failed: {str(e)}",
                "status": "error"
            }

    @staticmethod
    def analyze_prompt(prompt: str) -> Dict[str, Any]:
        """
        Generic method to analyze any prompt using OpenAI
        """
        try:
            analyzer = AIAnalyzer()
            response_text = analyzer.analyze_with_prompt(prompt)
            if response_text:
                return {
                    "analysis": response_text,
                    "status": "success"
                }
            else:
                return {
                    "analysis": "Analysis failed - no response received",
                    "status": "error"
                }
        except Exception as e:
            return {
                "analysis": f"Analysis failed: {str(e)}",
                "status": "error"
            }