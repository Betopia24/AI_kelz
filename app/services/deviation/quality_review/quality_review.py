import os
import json
import openai
from .quality_review_schema import PerMinuteReview, PerMinuteResponse, FinalQualityReview, FinalQualityReviewResponse
import re

class QualityReviewer:
    """
    Quality Review component that handles voice transcription, 
    AI analysis, and document processing
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



    def per_minute_review(self,input:PerMinuteReview ) -> PerMinuteResponse:
        prompt = f'''
                You are an expert pharmaceutical deviation investigation reviewer with 20+ years of experience in GMP, quality systems, and regulatory compliance. Your task is to analyze the following transcript and provide a comprehensive investigation analysis.

                Input Data:
                Transcription: {input.transcription}
                Existing Quality Review: {input.existing_quality_review or "Not provided"}
                Existing SME Review: {input.existing_sme_review or "Not provided"}

                If the existing quality review and SME review are not provided, base your analysis solely on the input transcription. Your analysis should address the following points for both the quality review and SME review:

                **Quality Review:**

                1. Has the investigation been completed satisfactorily?
                - Evaluate whether the investigation process appears thorough, and if all relevant aspects of the deviation have been adequately explored.

                2. Has an adequate root cause analysis been conducted, and are corrective and preventive actions (CAPA) identified to prevent reoccurrence?
                - Review whether the root cause analysis is clear and substantiated with data, and assess the robustness of the proposed CAPA actions.

                3. Have identified risks been discussed and mitigated?
                - Determine if risks related to the deviation have been identified, assessed, and whether effective mitigation strategies have been outlined.

                **SME Review:**

                1. Has the investigation been completed satisfactorily?
                - Determine whether the SME's review covers all critical aspects of the investigation, including completeness and attention to detail.

                2. Has an adequate root cause analysis been conducted, and are corrective and preventive actions (CAPA) identified to prevent reoccurrence?
                - Review the SME’s conclusions regarding root cause and CAPA. Are the proposed actions feasible and compliant with industry standards?

                3. Have identified risks been discussed and mitigated?
                - Assess whether the SME has adequately addressed the risks related to the deviation and whether appropriate measures to mitigate them have been proposed.

                Focus on identifying gaps or weaknesses in the investigation, root cause, and CAPA process, as well as potential risks that have or have not been properly mitigated.

                Return ONLY a valid JSON object with this exact structure:

                {{
                  "quality_review": "Comprehensive quality review analysis addressing investigation completeness, root cause analysis adequacy, CAPA effectiveness, and risk mitigation",
                  "sme_review": "Detailed SME review covering technical aspects, feasibility of proposed actions, compliance with industry standards, and overall assessment"
                }}
                '''

        response = self.get_openai_response(prompt)
        parsed_response = self.clean_and_parse_json(response)
        return PerMinuteResponse(**parsed_response)

    def final_review(self, input:FinalQualityReview) -> FinalQualityReviewResponse:
        prompt = f'''
                You are an expert pharmaceutical deviation investigation reviewer with 20+ years of experience in GMP, quality systems, and regulatory compliance. You will be given a audio transcript of the reviewer meeting along with existing investigation report.

                Using the provided existing investigation report channge based on the reviewer meeting transcript, produce a structured Final Quality Review Report in JSON format following this exact template format.

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
                Background: {input.existing_background}
                Discussion: {input.existing_discussion}
                Root Cause Analysis: {input.existing_root_cause_analysis}
                Final Assessment: {input.existing_final_assessment}
                Historic Review: {input.existing_historic_review}
                CAPA: {input.existing_capa}
                Attendees: {input.existing_attendees}

                Additional Data:
                Transcription for Review: {input.transcription}
                Document: {input.document or "Not provided"}

                Important Notes:
                - You are making changes to existing investigation report so whatever new things you add must start with /red and end with /red. So we can do track changes.
                - Include both transcription and document fields in your response.
                For example:
                "existing_background": "During routine final inspection of Batch 2023-012 at Plant 3, contamination was detected in the active pharmaceutical ingredient (API), resulting in a failure to meet required purity standards.Operators involved included John Doe (Quality Assurance Manager), Jane Smith (Manufacturing Supervisor), and Mark Johnson (Equipment Maintenance Lead). Immediate escalation was made upon discovery."
                "background": "During routine final inspection of Batch 2023-012 at Plant 3, contamination was detected in the active pharmaceutical ingredient (API), resulting in a failure to meet required purity standards./red The batch was produced using a newly installed automated mixing system /red. Operators involved included John Doe (Quality Assurance Manager), Jane Smith (Manufacturing Supervisor), and Mark Johnson (Equipment Maintenance Lead). Immediate escalation was made upon discovery."

                Return the complete JSON structure with ALL required fields including transcription and document.
                '''
        response = self.get_openai_response(prompt)
        parsed_response = self.clean_and_parse_json(response)
        return FinalQualityReviewResponse(**parsed_response)

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
            if response.startswith('```json'):
                response = response.replace('```json', '').replace('```', '').strip()
            elif response.startswith('```'):
                response = response.replace('```', '').strip()

            return json.loads(response)
        except json.JSONDecodeError as e:
            try:               
                response = re.sub(r'"([^"]*)"', lambda m: '"' + m.group(1).replace('\n', '\\n').replace('\r', '') + '"', response)
                return json.loads(response)
            except Exception:
                raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")

