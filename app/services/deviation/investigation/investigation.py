import re
import json
from app.services.utils.transcription import VoiceTranscriber
from app.services.deviation.investigation.investigation_schema import FirstTimeInvestigationRequest, InvestigationResponse,InvestigationRequest, FinalInvestigationReportResponse,RepeateInvestigationRequest
import openai
import os
class InvestigationService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


    def initial_investigation(self, input: FirstTimeInvestigationRequest) -> InvestigationResponse:
      prompt = f'''
              You are an expert pharmaceutical deviation investigator with 20+ years of experience in GMP, quality systems, and regulatory compliance. Analyze the following transcript and provide a comprehensive investigation analysis.

              CRITICAL INSTRUCTIONS:
              1. Even if specific sections
              2. Generate meaningful insights and recommendations based on the incident described
              3. Use pharmaceutical industry knowledge to fill gaps where transcript is unclear
              4. Provide actionable insights even from limited information
              5. Only use "Not found in document" if absolutely no relevant information or context exists for that specific field
              6. Think like a seasoned investigator - what would you look for, what questions would you ask, what actions would you recommend?

              Existing Background Details:{input.existing_background_details}
              Existing Impact Assessment:{input.existing_impact_assessment}
              Document Information:{input.document_information}

              Based on your analysis, provide a comprehensive investigation covering these areas:

              **Background**: Summarize the incident, what happened, when, where, and initial circumstances

              **Discussion**: 
                - Discuss Process: What process was involved, potential process failures or gaps
                - Equipment: Equipment involved, potential equipment issues or malfunctions  
                - Environment: Environmental factors affecting the incident
                - Documentation Is Adequate: "Yes" or "No" based on documentation review
                - External Communication: Discuss external communication (emails, forms, batch records etc) to support investigation
                - Personnel Training: Training adequacy and gaps identified
                - Equipment Qualification: Equipment qualification status and any issues
                
              **Root Cause Analysis**:
                - Fishbone Analysis: Complete fishbone diagram with all 6 categories (People, Method, Machine, Material, Environment, Measurement)
                - Five Why: Complete 5 Why analysis to identify root cause
                
              **Final Assessment**:
                - Patient Safety: Potential patient safety impact and risk level
                - Product Quality: Impact on product quality and specifications
                - Compliance Impact: GMP, regulatory compliance implications
                - Validation Impact: Impact on validated systems or processes
                - Regulatory Impact: Potential regulatory reporting or actions needed
                
              **Historic Review**: Previous occurrences, recurrence likelihood, historical context, and required investigation depth and CAPA scope
              
              **CAPA**:
                - Correction: Immediate fixes to address the specific incident
                - Interim Action: Short-term measures to prevent immediate recurrence
                - Corrective Action: Address root cause to prevent recurrence
                - Preventive Action: Broader measures to prevent similar issues

              Return ONLY a valid JSON object with this exact structure (all lowercase keys with underscores):

              {{
                "background": "Detailed background analysis based on the provided information",
                "discussion": {{
                  "discuss_process": "Process analysis and potential gaps",
                  "equipment": "Equipment factors and considerations",
                  "environment": "Environmental factors analysis", 
                  "documentation_is_adequate": "Yes or No - Documentation adequacy assessment",
                  "external_communication": "Analysis of external communication (emails, forms, batch records etc) to support investigation",
                  "personnel_training": "Personnel training assessment and gaps",
                  "equipment_qualification": "Equipment qualification status and issues"
                }},
                "root_cause_analysis": {{
                  "FishboneAnalysis": {{
                    "people": "Human factors and personnel-related root causes",
                    "method": "Process and procedure-related root causes",
                    "machine": "Equipment and machinery-related root causes",
                    "material": "Raw material and component-related root causes",
                    "environment": "Environmental factors contributing to root cause",
                    "measurement": "Measurement and monitoring system factors"
                  }},
                  "FiveWhy": "Complete 5 Why analysis - ask why 5 times to identify root cause"
                }},
                "final_assessment": {{
                  "patient_safety": "Patient safety impact assessment and risk level",
                  "product_quality": "Product quality impact and implications",
                  "compliance_impact": "Regulatory compliance and GMP implications", 
                  "validation_impact": "Impact on validated systems and processes",
                  "regulatory_impact": "Regulatory reporting and authority notification needs"
                }},
                "historic_review": "Assessment of previous occurrences, recurrence likelihood, historical context, and required investigation depth and CAPA scope",
                "capa": {{
                  "correction": "Immediate corrective measures to address the specific incident",
                  "interim_action": "Short-term actions to prevent immediate recurrence",
                  "corrective_action": "Root cause addressing actions to prevent recurrence", 
                  "preventive_action": "Preventive measures to avoid similar issues system-wide"
                }}
              }}
              '''
      response = self.get_openai_response(prompt)
      parsed_response = self.clean_and_parse_json(response)
      return InvestigationResponse(**parsed_response)

    def per_minute_investigation(self, input: InvestigationRequest) -> InvestigationResponse:
      prompt = f'''
              You are an expert pharmaceutical deviation investigator with 20+ years of experience in GMP, quality systems, and regulatory compliance. Analyze the following transcript and provide a comprehensive investigation analysis.
              
              Transcript: {input.transcript}
              
              Existing Investigation Data:
              Existing Background: {input.existing_background or "Not provided"}
              Existing Discussion: {input.existing_discussion or "Not provided"}
              Existing Root Cause Analysis: {input.existing_root_cause_analysis or "Not provided"}
              Existing Final Assessment: {input.existing_final_assessment or "Not provided"}
              Existing Historic Review: {input.existing_historic_review or "Not provided"}
              Existing CAPA: {input.existing_capa or "Not provided"}

              Based on your analysis, provide a comprehensive investigation covering these areas:

              **Background**: Summarize the incident, what happened, when, where, and initial circumstances

              **Discussion**: 
                - Discuss Process: What process was involved, potential process failures or gaps
                - Equipment: Equipment involved, potential equipment issues or malfunctions  
                - Environment: Environmental factors affecting the incident
                - Documentation Is Adequate: "Yes" or "No" based on documentation review
                - External Communication: Discuss external communication (emails, forms, batch records etc) to support investigation
                - Personnel Training: Training adequacy and gaps identified
                - Equipment Qualification: Equipment qualification status and any issues
                
              **Root Cause Analysis**:
                - Fishbone Analysis: Complete fishbone diagram with all 6 categories (People, Method, Machine, Material, Environment, Measurement)
                - Five Why: Complete 5 Why analysis to identify root cause
                
              **Final Assessment**:
                - Patient Safety: Potential patient safety impact and risk level
                - Product Quality: Impact on product quality and specifications
                - Compliance Impact: GMP, regulatory compliance implications
                - Validation Impact: Impact on validated systems or processes
                - Regulatory Impact: Potential regulatory reporting or actions needed
                
              **Historic Review**: Previous occurrences, recurrence likelihood, historical context, and required investigation depth and CAPA scope
              
              **CAPA**:
                - Correction: Immediate fixes to address the specific incident
                - Interim Action: Short-term measures to prevent immediate recurrence
                - Corrective Action: Address root cause to prevent recurrence
                - Preventive Action: Broader measures to prevent similar issues

              Return ONLY a valid JSON object with this exact structure (all lowercase keys with underscores):

              {{
                "background": "Detailed background analysis based on the provided information",
                "discussion": {{
                  "discuss_process": "Process analysis and potential gaps",
                  "equipment": "Equipment factors and considerations",
                  "environment": "Environmental factors analysis", 
                  "documentation_is_adequate": "Yes or No - Documentation adequacy assessment",
                  "external_communication": "Analysis of external communication (emails, forms, batch records etc) to support investigation",
                  "personnel_training": "Personnel training assessment and gaps",
                  "equipment_qualification": "Equipment qualification status and issues"
                }},
                "root_cause_analysis": {{
                  "FishboneAnalysis": {{
                    "people": "Human factors and personnel-related root causes",
                    "method": "Process and procedure-related root causes",
                    "machine": "Equipment and machinery-related root causes",
                    "material": "Raw material and component-related root causes",
                    "environment": "Environmental factors contributing to root cause",
                    "measurement": "Measurement and monitoring system factors"
                  }},
                  "FiveWhy": "Complete 5 Why analysis - ask why 5 times to identify root cause"
                }},
                "final_assessment": {{
                  "patient_safety": "Patient safety impact assessment and risk level",
                  "product_quality": "Product quality impact and implications",
                  "compliance_impact": "Regulatory compliance and GMP implications", 
                  "validation_impact": "Impact on validated systems and processes",
                  "regulatory_impact": "Regulatory reporting and authority notification needs"
                }},
                "historic_review": "Assessment of previous occurrences, recurrence likelihood, historical context, and required investigation depth and CAPA scope",
                "capa": {{
                  "correction": "Immediate corrective measures to address the specific incident",
                  "interim_action": "Short-term actions to prevent immediate recurrence",
                  "corrective_action": "Root cause addressing actions to prevent recurrence", 
                  "preventive_action": "Preventive measures to avoid similar issues system-wide"
                }}
              }}
              '''
      response = self.get_openai_response(prompt)
      parsed_response = self.clean_and_parse_json(response)
      return InvestigationResponse(**parsed_response)


    def final_investigation_report(self, input: InvestigationRequest) -> FinalInvestigationReportResponse:
      prompt = f'''
You are an expert pharmaceutical deviation investigator with 20+ years of experience in GMP, quality systems, and regulatory compliance. You will be given a audio transcript of the investigation meeting along with existing investigation information.

Using the provided existing investigation fragments, produce a structured Final Investigation Report in JSON format following this exact template format.

JSON Structure Required:

{{
  "background": "2-3 sentences describing what happened, when, where, who was involved, and immediate circumstances. Example: During in-process weight checks on Line 5, tablets were found below specification. Deviation identified by operators Michael E., Saidi M., and Rana S. Immediate escalation was made to QA.",
  "immediate_actions": "List the immediate steps taken when the deviation was discovered - quarantine, stopping processes, notifications, etc. Example: Quarantined all tablets from last compliant in-process check. Stopped compression until investigation. Secured machine and notified QA. Batch record and settings reviewed.",
  "discussion": "Cover Product Quality impact, Validation Impact, Compliance implications, Process controls, Equipment factors, Personnel factors, Documentation adequacy, and Most probable root cause statement. Include detailed analysis of the overall process, variables, environmental factors, equipment settings, validated parameters, documentation controls, SOPs, personnel training, equipment qualification, and maintenance. End with the most probable root cause statement.",
  "root_cause_analysis": {{
    "FishboneAnalysis": {{
      "machine": "Specific machine-related factors like feeder malfunction, compression force variation, tooling wear, speed and low fill",
      "material": "Material-related factors like blend flow issues, granule size variability, bulk density",
      "people": "Human factors like operator errors, training deficiencies, procedural non-compliance",
      "method": "Process-related factors like in-process check frequency, SOP adherence",
      "measurement": "Measurement system issues like equipment calibration, weight check accuracy",
      "environment": "Environmental factors like humidity/temperature affecting blend flow",
    }},
    "FiveWhy": "Complete 5 Why analysis for the root cause identification"
  }},
    "fishbone_diagram": [
      {{"machine": ["feeder malfunction", "compression force variation", "tooling wear", "speed and low fill"]}},
      {{"material": ["blend flow issues", "granule size variability", "bulk density"]}},
      {{"people": ["setup error", "adjustment deviation", "training gaps"]}},
      {{"method": ["in-process check frequency", "SOP adherence"]}},
      {{"measurement": ["equipment calibration", "weight check accuracy"]}},
      {{"environment": ["humidity/temperature affecting blend flow"]}}
    ],
  "historical_review": "Review of previous occurrences, trends, data analysis, equipment calibration/qualification records verification. Example: No recent findings; review of last 6 months deviations and PQR data ongoing. Equipment calibration/qualification records to be verified.",
  "capa": "CAPA plan to prevent and early detection of non-conformance. Include Correction (immediate fixes), Corrective Action (root cause prevention), and Preventive Action (system-wide improvements)",
  "impact_assessment": "Cover Patient Safety, Product Quality, and Validation impacts with specific risk levels and implications",
  "conclusion": "Deviation classification (Major/Minor), key findings, CAPA summary, and meeting attendees. Example: Major deviation due to product quality and validation impact. CAPA to include: investigation closure, operator retraining if required, equipment review, possible SOP/in-process check frequency update. Meeting attendees: [list names]."
}}

Existing Investigation Data:
Transcript: {input.transcript}
Background: {input.existing_background}
Discussion: {input.existing_discussion}
Root Cause Analysis: {input.existing_root_cause_analysis}
Final Assessment: {input.existing_final_assessment}
Historic Review: {input.existing_historic_review}
CAPA: {input.existing_capa}
Attendees: {input.exisiting_attendees}

Important Fishbone Diagram Requirements:
For each category (machine, material, people, method, measurement, environment), list a maximum of 2 reasons.
Each reason should be no longer than 2 words.

'''
      response = self.get_openai_response(prompt)
      parsed_response = self.clean_and_parse_json(response)
      
      return parsed_response
    
    def repeat_investigation(self, input:RepeateInvestigationRequest) -> FinalInvestigationReportResponse:
        # Build a strict prompt that maps inputs to the expected output schema exactly.
        prompt = f'''
                You are an expert pharmaceutical deviation investigation with 20+ years of experience in GMP, quality systems, and regulatory compliance. Change the existing investigation based on the new transcript provided. 
                Input (fields):
                transcription: {input.transcription}
                existing_background: {input.existing_background}
                existing_immediate_actions: {input.existing_immediate_actions}
                existing_discussion: {input.existing_discussion}
                existing_root_cause_analysis: {json.dumps(input.existing_root_cause_analysis)}
                existing_fishbone_diagram: {json.dumps(input.existing_fishbone_diagram)}
                existing_historic_review: {input.existing_historic_review}
                existing_capa: {input.existing_capa}
                existing_impact_assessment: {input.existing_impact_assessment}
                existing_conclusion: {input.existing_conclusion}

                JSON Structure Required:

                {{
                  "background": "2-3 sentences describing what happened, when, where, who was involved, and immediate circumstances. Example: During in-process weight checks on Line 5, tablets were found below specification. Deviation identified by operators Michael E., Saidi M., and Rana S. Immediate escalation was made to QA.",
                  "immediate_actions": "List the immediate steps taken when the deviation was discovered - quarantine, stopping processes, notifications, etc. Example: Quarantined all tablets from last compliant in-process check. Stopped compression until investigation. Secured machine and notified QA. Batch record and settings reviewed.",
                  "discussion": "Cover Product Quality impact, Validation Impact, Compliance implications, Process controls, Equipment factors, Personnel factors, Documentation adequacy, and Most probable root cause statement. Include detailed analysis of the overall process, variables, environmental factors, equipment settings, validated parameters, documentation controls, SOPs, personnel training, equipment qualification, and maintenance. End with the most probable root cause statement.",
                  "root_cause_analysis": {{
                    "FishboneAnalysis": {{
                      "machine": "Specific machine-related factors like feeder malfunction, compression force variation, tooling wear, speed and low fill",
                      "material": "Material-related factors like blend flow issues, granule size variability, bulk density",
                      "people": "Human factors like operator errors, training deficiencies, procedural non-compliance",
                      "method": "Process-related factors like in-process check frequency, SOP adherence",
                      "measurement": "Measurement system issues like equipment calibration, weight check accuracy",
                      "environment": "Environmental factors like humidity/temperature affecting blend flow",
                    }},
                    "FiveWhy": "Complete 5 Why analysis for the root cause identification"
                  }},
                    "fishbone_diagram": [
                      {{"machine": ["feeder malfunction", "compression force variation", "tooling wear", "speed and low fill"]}},
                      {{"material": ["blend flow issues", "granule size variability", "bulk density"]}},
                      {{"people": ["setup error", "adjustment deviation", "training gaps"]}},
                      {{"method": ["in-process check frequency", "SOP adherence"]}},
                      {{"measurement": ["equipment calibration", "weight check accuracy"]}},
                      {{"environment": ["humidity/temperature affecting blend flow"]}}
                    ],
                  "historical_review": "Review of previous occurrences, trends, data analysis, equipment calibration/qualification records verification. Example: No recent findings; review of last 6 months deviations and PQR data ongoing. Equipment calibration/qualification records to be verified.",
                  "capa": "CAPA plan to prevent and early detection of non-conformance. Include Correction (immediate fixes), Corrective Action (root cause prevention), and Preventive Action (system-wide improvements)",
                  "impact_assessment": "Cover Patient Safety, Product Quality, and Validation impacts with specific risk levels and implications",
                  "conclusion": "Deviation classification (Major/Minor), key findings, CAPA summary, and meeting attendees. Example: Major deviation due to product quality and validation impact. CAPA to include: investigation closure, operator retraining if required, equipment review, possible SOP/in-process check frequency update. Meeting attendees: [list names]."
                }}

                Important formatting rules:
                - The output MUST be valid JSON parseable by python's json.loads.
                - Do NOT include markdown, surrounding backticks, or explanatory text. Only output the JSON object.
                - Preserve the types: lists as JSON arrays, objects as JSON objects, strings as strings.

                Use the provided transcription and existing fields to produce the final report now.
                '''
        response = self.get_openai_response(prompt)
        parsed_response = self.clean_and_parse_json(response)
        return FinalInvestigationReportResponse(**parsed_response)
    
    def get_openai_response(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()
    
    def clean_and_parse_json(self, response: str) -> dict:
        """Clean AI response and parse as JSON, handling common formatting issues"""
        try:
            # Remove markdown code blocks if present
            if response.startswith('```json'):
                response = response.replace('```json', '').replace('```', '').strip()
            elif response.startswith('```'):
                response = response.replace('```', '').strip()
            
            # Try to parse the JSON
            return json.loads(response)
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to fix common issues
            try:
                # Replace actual newlines with \\n in string values
                import re
                # This regex finds content between quotes and replaces actual newlines with \n
                response = re.sub(r'"([^"]*)"', lambda m: '"' + m.group(1).replace('\n', '\\n').replace('\r', '') + '"', response)
                return json.loads(response)
            except Exception:
                raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")