import os
import json
import openai
from .quality_review_schema import PerMinuteReview, PerMinuteResponse, FinalQualityReviewRequest, FinalQualityReviewResponse,RepeatReviewRequest
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

                Write the reviews in points. They need to be short. Return ONLY a valid JSON object with this exact structure:

                {{
                  "quality_review": "Comprehensive quality review analysis addressing investigation completeness, root cause analysis adequacy, CAPA effectiveness, and risk mitigation",
                  "sme_review": "Detailed SME review covering technical aspects, feasibility of proposed actions, compliance with industry standards, and overall assessment"
                }}
                '''

        response = self.get_openai_response(prompt)
        parsed_response = self.clean_and_parse_json(response)
        return PerMinuteResponse(**parsed_response)

    def final_review(self, input:FinalQualityReviewRequest) -> FinalQualityReviewResponse:
        # Build a strict prompt that maps inputs to the expected output schema exactly.
        prompt = f'''
                You are an expert pharmaceutical deviation investigation reviewer with 20+ years of experience in GMP, quality systems, and regulatory compliance.

                You will be provided with the following input object. Use this data to produce a Final Quality Review JSON that exactly matches the FinalQualityReviewResponse schema.

                Input (fields):
                transcription: {input.transcription}
                document: {json.dumps(input.document) if input.document else 'Not provided'}
                existing_background: {input.existing_background}
                existing_immediate_actions: {input.existing_immediate_actions}
                existing_discussion: {input.existing_discussion}
                existing_root_cause_analysis: {json.dumps(input.existing_root_cause_analysis)}
                existing_fishbone_diagram: {json.dumps(input.existing_fishbone_diagram)}
                existing_historic_review: {input.existing_historic_review}
                existing_capa: {input.existing_capa}
                existing_impact_assessment: {input.existing_impact_assessment}
                existing_conclusion: {input.existing_conclusion}

                Instructions:
                - Use the input data to update/augment the existing investigation where appropriate. When you add new or changed text within existing fields, wrap additions with /red and /red to enable simple change-tracking.
                - Return ONLY a single JSON object that exactly matches this structure (FinalQualityReviewResponse):

                {{
                  "background": "<2-3 sentence updated background>",
                  "immediate_actions": "<immediate actions, include /red wrapped additions>",
                  "discussion": "<detailed discussion, include /red wrapped additions>",
                  "root_cause_analysis": <list of dicts or objects describing root cause analysis (use existing_root_cause_analysis as base)>,
                  "fishbone_diagram": <list of dicts representing the fishbone diagram (use existing_fishbone_diagram as base)>,
                  "historical_review": "<historical review summary, include /red wrapped additions>",
                  "capa": "<CAPA summary, include /red wrapped additions>",
                  "impact_assessment": "<impact assessment summary, include /red wrapped additions>",
                  "conclusion": "<concise conclusion and deviation classification>",
                }}

                Important formatting rules:
                - The output MUST be valid JSON parseable by python's json.loads.
                - Do NOT include markdown, surrounding backticks, or explanatory text. Only output the JSON object.
                - Preserve the types: lists as JSON arrays, objects as JSON objects, strings as strings.
                - Use /red markers only around newly added or changed text inside string fields.

                Use the provided transcription and existing fields to produce the final report now.
                '''
        response = self.get_openai_response(prompt)
        parsed_response = self.clean_and_parse_json(response)
        return FinalQualityReviewResponse(**parsed_response)
    

    def repeat_review(self, input:RepeatReviewRequest) -> FinalQualityReviewResponse:
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
                - Preserve /red markers that is already there.
                - DO NOT add new /red markers.

                Use the provided transcription and existing fields to produce the final report now.
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

