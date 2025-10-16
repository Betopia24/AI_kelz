import re
import json
from app.services.utils.transcription import VoiceTranscriber
from app.services.deviation.investigation_new.investigation_new_schema import FirstTimeInvestigationRequest, InvestigationResponse,InvestigationRequest
import openai
import os
class InvestigationService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


    def initial_investigation(self, input: InvestigationRequest) -> InvestigationResponse:
      prompt = f'''
              You are an expert pharmaceutical deviation investigator with 20+ years of experience in GMP, quality systems, and regulatory compliance. Analyze the following transcript and provide a comprehensive investigation analysis.

              CRITICAL INSTRUCTIONS:
              1. Even if specific sections are not explicitly mentioned, use your pharmaceutical expertise to provide reasonable analysis based on context clues, industry standards, and best practices
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
                - Process: What process was involved, potential process failures or gaps
                - Equipment: Equipment involved, potential equipment issues or malfunctions  
                - Environment/People: Environmental factors, human factors, training issues
                - Is Documentation Adequate:"Yes" or "No" or "" if unknown
                - external_communication: Discuss interview external communication (emails, forms, batch records etc) to support investigation.
                - personnel_training
                - equipment_qualification
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
      response = self.get_openai_response(prompt)
      return InvestigationResponse(**json.loads(response))

def per_minute_investigation(self, input: InvestigationRequest) -> InvestigationResponse:
      prompt = f'''
              You are an expert pharmaceutical deviation investigator with 20+ years of experience in GMP, quality systems, and regulatory compliance. Analyze the following transcript and provide a comprehensive investigation analysis.
              
              Existing Background :{input.existing_background}
              Existing Discussion :{input.existing_discussion}
              Existing Root Cause Analysis :{input.existing_root_cause_analysis}
              Existing Final Assessment :{input.existing_final_assessment}
              Existing Historic Review :{input.existing_historic_review}
              Existing CAPA :{input.existing_capa}
              '''
      response = self.get_openai_response(prompt)
      return InvestigationResponse(**json.loads(response))


def final_investigation(self, input: InvestigationRequest) -> InvestigationResponse:
      prompt = f'''
              You are an expert pharmaceutical deviation investigator with 20+ years of experience in GMP, quality systems, and regulatory compliance. Analyze the following transcript and provide a comprehensive investigation analysis.
              
              Existing Background :{input.existing_background}
              Existing Discussion :{input.existing_discussion}
              Existing Root Cause Analysis :{input.existing_root_cause_analysis}
              Existing Final Assessment :{input.existing_final_assessment}
              Existing Historic Review :{input.existing_historic_review}
              Existing CAPA :{input.existing_capa}
              '''
      response = self.get_openai_response(prompt)
      return InvestigationResponse(**json.loads(response))
        
def get_openai_response(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return completion.choices[0].message.content.strip()