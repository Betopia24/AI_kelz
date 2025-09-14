import re
import json
from app.services.utils.transcription import VoiceTranscriber
from app.services.utils.ai_analysis import AIAnalyzer

class InvestigationService:
    @staticmethod
    def analyze_voice_file(voice_file_path: str) -> dict:
        # Step 1: Transcribe the voice file
        transcriber = VoiceTranscriber()
        transcribed_text = transcriber.transcribe_audio(voice_file_path)
        if not transcribed_text or not transcribed_text.strip():
            return {"error": "Transcription failed or returned empty text."}
        return InvestigationService.analyze_transcript(transcribed_text)

    @staticmethod
    def analyze_transcript(transcribed_text: str) -> dict:
        from app.services.utils.ai_analysis import AIAnalyzer

        # Enhanced prompt that encourages inference and analysis
        prompt = f'''
You are an expert pharmaceutical deviation investigator with 20+ years of experience in GMP, quality systems, and regulatory compliance. Analyze the following transcript and provide a comprehensive investigation analysis.

CRITICAL INSTRUCTIONS:
1. Even if specific sections are not explicitly mentioned, use your pharmaceutical expertise to provide reasonable analysis based on context clues, industry standards, and best practices
2. Generate meaningful insights and recommendations based on the incident described
3. Use pharmaceutical industry knowledge to fill gaps where transcript is unclear
4. Provide actionable insights even from limited information
5. Only use "Not found in document" if absolutely no relevant information or context exists for that specific field
6. Think like a seasoned investigator - what would you look for, what questions would you ask, what actions would you recommend?

TRANSCRIPT TO ANALYZE:
"""{transcribed_text}"""

Based on your analysis, provide a comprehensive investigation covering these areas:

**Background**: Summarize the incident, what happened, when, where, and initial circumstances
**Deviation Triage**: Classify severity, impact level, immediate risk assessment
**Discussion**: 
  - Process: What process was involved, potential process failures or gaps
  - Equipment: Equipment involved, potential equipment issues or malfunctions  
  - Environment/People: Environmental factors, human factors, training issues
  - Documentation: Document adequacy, procedure compliance, record keeping
**Root Cause Analysis**:
  - 5 Why: Recommend 5 Why analysis approach for this incident type
  - Fishbone: Suggest Fishbone categories relevant to this deviation
  - 5Ms: Analyze Man, Machine, Method, Material, Measurement factors
  - FMEA: Recommend FMEA approach if applicable
**Final Assessment**:
  - Patient Safety: Potential patient safety impact and risk level
  - Product Quality: Impact on product quality and specifications
  - Compliance Impact: GMP, regulatory compliance implications
  - Validation Impact: Impact on validated systems or processes
  - Regulatory Impact: Potential regulatory reporting or actions needed
**Historic Review**:
  - Previous Occurrence: Likelihood this has occurred before based on incident type
  - RCA/CAPA Adequacy: Assessment of what investigation depth and CAPA scope needed
**CAPA**:
  - Correction: Immediate fixes to address the specific incident
  - Interim Action: Short-term measures to prevent immediate recurrence
  - Corrective Action: Address root cause to prevent recurrence
  - Preventive Action: Broader measures to prevent similar issues
**Investigation Summary**: Comprehensive summary including key findings, conclusions, and overall assessment

Return ONLY a valid JSON object with this exact structure (use underscores in key names):

{{
  "Background": "Detailed background analysis based on transcript",
  "Deviation_Triage": "Triage classification and risk assessment", 
  "Discussion": {{
    "process": "Process analysis and potential gaps",
    "equipment": "Equipment factors and considerations",
    "environment_people": "Environmental and human factors analysis", 
    "documentation": "Documentation adequacy assessment"
  }},
  "Root_Cause_Analysis": {{
    "5_why": "5 Why methodology recommendation and initial analysis",
    "Fishbone": "Fishbone analysis categories and approach",
    "5Ms": "5Ms analysis covering all relevant factors",
    "FMEA": "FMEA recommendation and applicability"
  }},
  "Final_Assessment": {{
    "Patient_Safety": "Patient safety impact assessment and risk level",
    "Product_Quality": "Product quality impact and implications",
    "Compliance_Impact": "Regulatory compliance and GMP implications", 
    "Validation_Impact": "Impact on validated systems and processes",
    "Regulatory_Impact": "Regulatory reporting and authority notification needs"
  }},
  "Historic_Review": {{
    "previous_occurrence": "Assessment of recurrence likelihood and historical context",
    "impact_to_adequacy_of_RCA_and_CAPA": "Required investigation depth and CAPA scope assessment"
  }},
  "CAPA": {{
    "Correction": "Immediate corrective measures to address the specific incident",
    "Interim_Action": "Short-term actions to prevent immediate recurrence",
    "Corrective_Action": "Root cause addressing actions to prevent recurrence", 
    "Preventive_Action": "Preventive measures to avoid similar issues system-wide"
  }},
  "Investigation_Summary": "Comprehensive investigation summary with key findings, conclusions, risk assessment, and overall incident characterization"
}}
'''
        ai = AIAnalyzer()
        ai_response = ai.analyze_with_prompt(prompt)
        if not ai_response:
            return {"error": "AI analysis failed - no response received"}
        ai_result = {}
        json_match = re.search(r'({[\s\S]*})', ai_response)
        if json_match:
            try:
                ai_result = json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                ai_result = {"error": f"JSON parsing failed: {str(e)}"}
        else:
            try:
                ai_result = json.loads(ai_response)
            except json.JSONDecodeError as e:
                ai_result = {"error": "Response is not valid JSON", "raw_response": ai_response[:500]}
        return ai_result

    @staticmethod
    def analyze_simple_input(incident_description: str, background_information: str, initial_observations: str) -> dict:
        """
        Analyze investigation using 3 string inputs: incident description, background, and observations.
        
        Args:
            incident_description: Description of the incident/deviation
            background_information: Background context and circumstances
            initial_observations: Initial findings and observations
        
        Returns:
            dict: Investigation analysis results
        """
        from app.services.utils.ai_analysis import AIAnalyzer
        
        # Combine the three input fields into a structured transcript
        combined_input = f"""
INCIDENT DESCRIPTION:
{incident_description}

BACKGROUND INFORMATION:
{background_information}

INITIAL OBSERVATIONS:
{initial_observations}
"""
        
        # Enhanced prompt for 3-field input analysis
        prompt = f'''
You are an expert pharmaceutical deviation investigator with 20+ years of experience in GMP, quality systems, and regulatory compliance. Analyze the following incident information and provide a comprehensive investigation analysis.

The incident information has been provided in three structured sections:
1. INCIDENT DESCRIPTION - What happened
2. BACKGROUND INFORMATION - Context and circumstances 
3. INITIAL OBSERVATIONS - Initial findings and immediate actions

CRITICAL INSTRUCTIONS:
1. Use your pharmaceutical expertise to provide comprehensive analysis based on the provided information
2. Generate meaningful insights and recommendations based on the incident described
3. Apply pharmaceutical industry knowledge to fill gaps and provide context
4. Provide actionable insights and professional recommendations
5. Think like a seasoned investigator - analyze all aspects systematically
6. Only use "Not found in document" if absolutely no relevant information exists for a specific field

INCIDENT INFORMATION TO ANALYZE:
"""{combined_input}"""

Based on your analysis of the incident description, background information, and initial observations, provide a comprehensive investigation covering these areas:

**Background**: Synthesize the incident details, timeline, location, and circumstances from all three input sections
**Deviation Triage**: Classify severity, impact level, immediate risk assessment based on the incident type and observations
**Discussion**: 
  - Process: Analyze the process involved, potential failures or gaps based on the incident
  - Equipment: Equipment factors, potential issues or malfunctions mentioned or implied
  - Environment/People: Environmental factors, human factors, training considerations
  - Documentation: Documentation adequacy, procedure compliance, record keeping issues
**Root Cause Analysis**:
  - 5 Why: Recommend 5 Why analysis approach tailored to this specific incident
  - Fishbone: Suggest relevant Fishbone categories for this deviation type
  - 5Ms: Analyze Man, Machine, Method, Material, Measurement factors
  - FMEA: Recommend FMEA approach if applicable to this incident type
**Final Assessment**:
  - Patient Safety: Assess patient safety impact and risk level
  - Product Quality: Evaluate impact on product quality and specifications
  - Compliance Impact: Determine GMP and regulatory compliance implications
  - Validation Impact: Assess impact on validated systems or processes
  - Regulatory Impact: Evaluate regulatory reporting or authority notification needs
**Historic Review**:
  - Previous Occurrence: Assess likelihood of previous occurrences based on incident characteristics
  - RCA/CAPA Adequacy: Recommend investigation depth and CAPA scope needed
**CAPA**:
  - Correction: Immediate fixes to address this specific incident
  - Interim Action: Short-term measures to prevent immediate recurrence
  - Corrective Action: Address root cause to prevent recurrence
  - Preventive Action: Broader measures to prevent similar issues system-wide
**Investigation Summary**: Comprehensive summary with key findings, conclusions, and overall assessment

Return ONLY a valid JSON object with this exact structure (use underscores in key names):

{{
  "Background": "Detailed background analysis synthesizing all provided information",
  "Deviation_Triage": "Triage classification and risk assessment based on incident details", 
  "Discussion": {{
    "process": "Process analysis and potential gaps based on incident information",
    "equipment": "Equipment factors and considerations from observations",
    "environment_people": "Environmental and human factors analysis", 
    "documentation": "Documentation adequacy assessment"
  }},
  "Root_Cause_Analysis": {{
    "5_why": "5 Why methodology recommendation and initial analysis framework",
    "Fishbone": "Fishbone analysis categories and approach for this incident type",
    "5Ms": "5Ms analysis covering all relevant factors",
    "FMEA": "FMEA recommendation and applicability assessment"
  }},
  "Final_Assessment": {{
    "Patient_Safety": "Patient safety impact assessment and risk level determination",
    "Product_Quality": "Product quality impact and implications analysis",
    "Compliance_Impact": "Regulatory compliance and GMP implications assessment", 
    "Validation_Impact": "Impact on validated systems and processes evaluation",
    "Regulatory_Impact": "Regulatory reporting and authority notification requirements"
  }},
  "Historic_Review": {{
    "previous_occurrence": "Assessment of recurrence likelihood and historical context",
    "impact_to_adequacy_of_RCA_and_CAPA": "Required investigation depth and CAPA scope assessment"
  }},
  "CAPA": {{
    "Correction": "Immediate corrective measures to address the specific incident",
    "Interim_Action": "Short-term actions to prevent immediate recurrence",
    "Corrective_Action": "Root cause addressing actions to prevent recurrence", 
    "Preventive_Action": "Preventive measures to avoid similar issues system-wide"
  }},
  "Investigation_Summary": "Comprehensive investigation summary with key findings, conclusions, risk assessment, and overall incident characterization based on all provided information"
}}
'''

        ai = AIAnalyzer()
        ai_response = ai.analyze_with_prompt(prompt)
        
        if not ai_response:
            return {"error": "AI analysis failed - no response received"}
        
        ai_result = {}
        json_match = re.search(r'({[\s\S]*})', ai_response)
        if json_match:
            try:
                ai_result = json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                ai_result = {"error": f"JSON parsing failed: {str(e)}"}
        else:
            try:
                ai_result = json.loads(ai_response)
            except json.JSONDecodeError as e:
                ai_result = {"error": "Response is not valid JSON", "raw_response": ai_response[:500]}
        
        return ai_result

    @staticmethod
    def validate_simple_input(incident_description: str, background_information: str, initial_observations: str) -> dict:
        """
        Validate the 3 string inputs before processing.
        
        Args:
            incident_description: Description of the incident/deviation
            background_information: Background context and circumstances
            initial_observations: Initial findings and observations
        
        Returns:
            dict: Validation results with status and issues
        """
        validation_issues = []
        
        # Check if fields are empty or too short
        if not incident_description or len(incident_description.strip()) < 10:
            validation_issues.append("Incident description must be at least 10 characters long")
        
        if not background_information or len(background_information.strip()) < 10:
            validation_issues.append("Background information must be at least 10 characters long")
            
        if not initial_observations or len(initial_observations.strip()) < 10:
            validation_issues.append("Initial observations must be at least 10 characters long")
        
        # Check for overly long inputs
        if len(incident_description) > 5000:
            validation_issues.append("Incident description exceeds maximum length of 5000 characters")
            
        if len(background_information) > 5000:
            validation_issues.append("Background information exceeds maximum length of 5000 characters")
            
        if len(initial_observations) > 5000:
            validation_issues.append("Initial observations exceeds maximum length of 5000 characters")
        
        # Check for potential quality issues
        if incident_description.lower() == background_information.lower():
            validation_issues.append("Incident description and background information appear to be identical")
            
        if incident_description.lower() == initial_observations.lower():
            validation_issues.append("Incident description and initial observations appear to be identical")
        
        return {
            "is_valid": len(validation_issues) == 0,
            "validation_issues": validation_issues,
            "total_length": len(incident_description) + len(background_information) + len(initial_observations),
            "field_lengths": {
                "incident_description": len(incident_description),
                "background_information": len(background_information),
                "initial_observations": len(initial_observations)
            }
        }

    @staticmethod
    def generate_investigation_summary(analysis_result: dict) -> str:
        """
        Generate a brief summary from the full investigation analysis.
        
        Args:
            analysis_result: Complete investigation analysis dictionary
            
        Returns:
            str: Brief investigation summary
        """
        try:
            if "error" in analysis_result:
                return f"Investigation analysis failed: {analysis_result.get('error', 'Unknown error')}"
            
            # Extract key information for summary
            background = analysis_result.get("Background", "No background available")
            triage = analysis_result.get("Deviation_Triage", "No triage classification")
            summary = analysis_result.get("Investigation_Summary", "No summary available")
            
            # Create a concise summary
            brief_summary = f"""
INVESTIGATION SUMMARY:
{summary[:200]}{'...' if len(summary) > 200 else ''}

KEY CLASSIFICATION: {triage[:100]}{'...' if len(triage) > 100 else ''}

BACKGROUND: {background[:150]}{'...' if len(background) > 150 else ''}
""".strip()
            
            return brief_summary
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    @staticmethod
    def extract_key_findings(analysis_result: dict) -> dict:
        """
        Extract key findings from the complete investigation analysis.
        
        Args:
            analysis_result: Complete investigation analysis dictionary
            
        Returns:
            dict: Key findings summary
        """
        try:
            if "error" in analysis_result:
                return {"error": analysis_result["error"]}
            
            # Extract key components
            final_assessment = analysis_result.get("Final_Assessment", {})
            capa = analysis_result.get("CAPA", {})
            root_cause = analysis_result.get("Root_Cause_Analysis", {})
            
            key_findings = {
                "patient_safety_impact": final_assessment.get("Patient_Safety", "Not assessed"),
                "product_quality_impact": final_assessment.get("Product_Quality", "Not assessed"),
                "compliance_impact": final_assessment.get("Compliance_Impact", "Not assessed"),
                "immediate_correction": capa.get("Correction", "None specified"),
                "corrective_action": capa.get("Corrective_Action", "None specified"),
                "preventive_action": capa.get("Preventive_Action", "None specified"),
                "root_cause_summary": root_cause.get("5_why", "Root cause analysis pending"),
                "overall_summary": analysis_result.get("Investigation_Summary", "Summary not available")
            }
            
            return key_findings
            
        except Exception as e:
            return {"error": f"Error extracting key findings: {str(e)}"}

    @staticmethod
    def format_investigation_report(analysis_result: dict, input_data: dict = None) -> str:
        """
        Format the investigation analysis into a readable report.
        
        Args:
            analysis_result: Complete investigation analysis dictionary
            input_data: Optional original input data
            
        Returns:
            str: Formatted investigation report
        """
        try:
            if "error" in analysis_result:
                return f"INVESTIGATION REPORT - ERROR\n{'='*50}\nError: {analysis_result['error']}"
            
            report = f"""
PHARMACEUTICAL DEVIATION INVESTIGATION REPORT
{'='*60}

BACKGROUND
{'-'*20}
{analysis_result.get('Background', 'Not available')}

DEVIATION TRIAGE
{'-'*20}
{analysis_result.get('Deviation_Triage', 'Not available')}

DISCUSSION
{'-'*20}
Process: {analysis_result.get('Discussion', {}).get('process', 'Not analyzed')}

Equipment: {analysis_result.get('Discussion', {}).get('equipment', 'Not analyzed')}

Environment/People: {analysis_result.get('Discussion', {}).get('environment_people', 'Not analyzed')}

Documentation: {analysis_result.get('Discussion', {}).get('documentation', 'Not analyzed')}

ROOT CAUSE ANALYSIS
{'-'*20}
5 Why Analysis: {analysis_result.get('Root_Cause_Analysis', {}).get('5_why', 'Not performed')}

Fishbone Analysis: {analysis_result.get('Root_Cause_Analysis', {}).get('Fishbone', 'Not performed')}

5Ms Analysis: {analysis_result.get('Root_Cause_Analysis', {}).get('5Ms', 'Not performed')}

FINAL ASSESSMENT
{'-'*20}
Patient Safety: {analysis_result.get('Final_Assessment', {}).get('Patient_Safety', 'Not assessed')}

Product Quality: {analysis_result.get('Final_Assessment', {}).get('Product_Quality', 'Not assessed')}

Compliance Impact: {analysis_result.get('Final_Assessment', {}).get('Compliance_Impact', 'Not assessed')}

Regulatory Impact: {analysis_result.get('Final_Assessment', {}).get('Regulatory_Impact', 'Not assessed')}

CAPA RECOMMENDATIONS
{'-'*20}
Correction: {analysis_result.get('CAPA', {}).get('Correction', 'Not specified')}

Interim Action: {analysis_result.get('CAPA', {}).get('Interim_Action', 'Not specified')}

Corrective Action: {analysis_result.get('CAPA', {}).get('Corrective_Action', 'Not specified')}

Preventive Action: {analysis_result.get('CAPA', {}).get('Preventive_Action', 'Not specified')}

INVESTIGATION SUMMARY
{'-'*20}
{analysis_result.get('Investigation_Summary', 'Summary not available')}

HISTORIC REVIEW
{'-'*20}
Previous Occurrences: {analysis_result.get('Historic_Review', {}).get('previous_occurrence', 'Not reviewed')}

RCA/CAPA Adequacy: {analysis_result.get('Historic_Review', {}).get('impact_to_adequacy_of_RCA_and_CAPA', 'Not assessed')}

{'='*60}
Report Generated: {analysis_result.get('timestamp', 'Not specified')}
"""
            return report.strip()
            
        except Exception as e:
            return f"ERROR FORMATTING REPORT: {str(e)}"