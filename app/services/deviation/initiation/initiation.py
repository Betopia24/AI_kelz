import os
import json
import openai
from fastapi import HTTPException
from dotenv import load_dotenv
from app.services.deviation.initiation.initiation_schema import PerMinuteInitiationRequest, PerMinuteInitiationResponse, FinalCheckRequest, FinalRequest, FormalIncidentReport, IncidentReportSection, ModifyIncidentReportRequest

load_dotenv()

class Initiation:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    

    def get_per_minute_summary(self, input_data: PerMinuteInitiationRequest) -> PerMinuteInitiationResponse:
        import json
        

        prompt= self.create_prompt(input_data)
        response = self.get_openai_response(prompt).strip()
        print("Raw model response:", response)

        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError as e:
            print("Model response:", response)
            raise HTTPException(status_code=500, detail="Failed to parse model response as JSON.")

        return PerMinuteInitiationResponse(**response_dict)

    def create_prompt(self, input_data: PerMinuteInitiationRequest) -> str:
        return  f"""
                You are a language model that receives audio transcriptions related to quality and change management processes. Your task is to analyze the transcription and extract structured meeting information.

                The following are the inputs:

                - {input_data.incident_title}: (Optional) Previously extracted incident title, if any. If it exists, use it unless in transcription there is a specific mention; if not, generate a new one.
                - {input_data.transcribed_text}: The full transcript up to this point (latest cumulative 10-second update).
                - {input_data.background_details}: (Optional) Previously extracted background details, if any.
                - {input_data.background_attendee}: (Optional) List of previously known attendee names.
                - {input_data.impact_assessment}: (Optional) Previously extracted impact assessment data, if any.
                - {input_data.criticality}: (Optional) Previously extracted criticality, if any.

                ---

                Your output must follow this strict JSON schema with exactly **three fields**:

                1. Incident Title (string):Previously extracted incident title, if any. If it exists, use it unless in transcription there is a specific mention; if not, generate a new one.
                
                2."background_details" (json): A JSON object with the following keys:
                    - "Who"
                    - "What"
                    - "Where"
                    - "Immediate_Action"
                    - "Quality_Concerns"
                    - "Quality_Controls"
                    - "RCA_tool"
                    - "Expected_Interim_Action"
                    - "CAPA"

                    ⚠️ Each field must be included, even if not mentioned — in that case, return an empty string "".

                ---

                3. "background_attendee" (List of String): A list of attendee names. If none are found, return an empty list.

                ---

                4. "impact_assessment" (json): A Nested JSON object with three fields:
                    - "Product Quality"
                    - "Patient Safety"
                    - "Regulatory Impact"
                    - "Validation Impact"

                Each of these three fields must be an dictionary object with:
                    - `"impact"`: "Yes" or "No".
                    - `"severity"`: One of "Low", "Medium", "High" if impact is "Yes", or "" if impact is "No".

                ✅ Examples:
                - "Product_Quality": {{ "impact": "Yes", "severity": "Medium" }}
                - "Patient_Safety": {{ "impact": "No", "severity": "" }}

                5. "criticality" (string): The criticality level of the incident "Major" or "Minor". If you can't determine the criticality or not mentioned explicitly, return an empty string.

                ---

                ### Instructions:

                1. Correct any transcription errors in `input.transcribed_text`.
                2. Use the full transcript to extract structured information.
                3. Incorporate previously extracted details (from `input.background_details`, etc.) where applicable.
                4. If new information contradicts or improves prior data, update it.
                5. All keys must be present in the output structure.
                6. Respond ONLY with valid JSON — no markdown, no explanations, no code blocks.

                ---

                ### Example Input Object:

                {{
                "input": {{
                    "transcribed_text": "The team reviewed the updated templates and agreed that no immediate action was required.",
                    "background_details": null,
                    "background_attendee": ["Alice", "Bob"],
                    "impact_assessment": null
                }}
                }}

                ---

                ### Example Output:

                
                {{
                "incident_title": "Deviation 0059 CAPA Review",
                "background_details": {{
                    "Who": "...",
                    "What": "...",
                    "Where": "...",
                    "Immediate_Action": "...",
                    "Quality_Concerns": "...",
                    "RCA_tool": "...",
                    "Expected_Interim_Action": "...",
                    "Product_Quality": "...",
                    "Expected Interim Action": "...",
                    "CAPA": "..."
                }},
                "background_attendee": "[ Alice, Bob, Charlie ]",
                "impact_assessment": {{
                    "Product_Quality": {{
                    "impact": "Yes",
                    "severity": "Medium"
                    }},
                    "Patient_Safety": {{
                    "impact": "No",
                    "severity": ""
                    }},
                    "Regulatory_Impact": {{
                    "impact": "Yes",
                    "severity": "Low"
                    }},
                    
                    "Validation_Impact": {{
                    "impact": "Yes",
                    "severity": "Low"
                    }}
                }},
                "criticality": "Major"
                }}
                """

                

    
    def get_openai_response (self, prompt:str)->str:
        completion =self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7            
        )
        return completion.choices[0].message.content



    def check_initiation_details (self,input:FinalCheckRequest):
        prompt = f"""
                You are a helpful assistant for analyzing structured meeting data.

                Input data: {input.background_details}

                Your task is to check **which fields have not been filled yet** — i.e., which fields have empty string values ("").

                ### Instructions:
                - If there are any fields missing, return a sentence listing their names in a natural way.
                - For one missing field, the sentence should be like: 
                    - "You haven't mentioned [Field]."
                - For multiple missing fields, format the sentence like:
                    - "You haven't talked about [Field 1], [Field 2], and [Field 3]."
                - For all missing fields, you can say:
                    - "You haven't talked about [Field 1], [Field 2], [Field 3], [Field 4], and [Field 5]."
                - If all fields are filled, respond exactly with:
                - "All background details have been provided."
                - Do not include any explanations, markdown, or code. Only return the final sentence that can be shown directly to a user.

                ---

                Example input:

                background_details = {{
                    "Who": "Bob and Alice from QA",
                    "What": "CAPA review for deviation 0059 flagged during last week's internal audit",
                    "Where": "",
                    "Immediate_Action": "",
                    "Quality_Concerns": "",
                    "Quality_Controls": "",
                    "RCA_tool": "fishbone diagram",
                    "Expected_Interim_Action": "",
                    "CAPA": ""
                }}

                ### Expected output:
                "You haven't talked about Where, Immediate Action, Quality Concerns, Expected Interim Action, and CAPA."

                                """

        response = self.get_openai_response(prompt).strip()
        return response
        
    def generate_formal_incident_report(self, input_data: FinalRequest) -> FormalIncidentReport:
        """
        Generates a formal incident report with specific sections based on transcription and existing data.
        
        Args:
            input_data: The FinalRequest object containing transcription and any existing information
            
        Returns:
            FormalIncidentReport: A structured incident report with all required sections
        """
        prompt = self.create_incident_report_prompt(input_data)
        response = self.get_openai_response(prompt)
        
        try:
            report_sections = json.loads(response)
            
            formal_report = FormalIncidentReport(
                incident_title=IncidentReportSection(content=report_sections["incident_title"]),
                background=IncidentReportSection(content=report_sections["background"]),
                meeting_attendees=IncidentReportSection(content=report_sections["meeting_attendees"]),
                impact_assessment=IncidentReportSection(content=report_sections["impact_assessment"]),
                criticality=IncidentReportSection(content=report_sections["criticality"])
            )
            return formal_report
            
        except json.JSONDecodeError as e:
            print("Raw response:", response)
            raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON")
        except KeyError as e:
            print("Raw response:", response)
            raise HTTPException(status_code=500, detail=f"Missing required section in response: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating incident report: {str(e)}")
    
    def create_incident_report_prompt(self, input_data: FinalRequest) -> str:
        """
        Creates the prompt for generating a formal incident report.
        
        Args:
            input_data: The FinalRequest object containing transcription and existing data
            
        Returns:
            str: The complete prompt for the AI
        """
        return f"""
        You are an expert AI assistant for pharmaceutical quality management and deviation reporting.
        Your task is to generate a formal incident report based on the transcription and any existing details provided.
        
        ## INPUT DATA:
        - Transcribed text: {input_data.transcribed_text}
        - Incident title: {input_data.incident_title if input_data.incident_title else "Not provided"}
        - Background details: {json.dumps(input_data.background_details) if input_data.background_details else "Not provided"}
        - Meeting attendees: {json.dumps(input_data.background_attendee) if input_data.background_attendee else "Not provided"}
        - Impact assessment: {json.dumps(input_data.impact_assessment) if input_data.impact_assessment else "Not provided"}

        ## OUTPUT FORMAT:
        Generate a structured incident report with the following 5 main sections. Your response must be a JSON object with these exact sections:
        
        {{
            "incident_title": "1. Incident Title [Title] \\nDeviation ID: [To be assigned] \\nDate/Time of Occurrence: [Date], [Time] hrs \\nLocation: [Location] \\nProduct: [Product Name] \\nDosage Form: [Form]",
            
            "background": "2. Background \\n[Detailed description of what happened] \\n\\nPersonnel involved include [list of names] \\n\\nImmediate Action \\n[Actions taken immediately after detection] \\n\\nQuality Concerns/Controls \\n[Quality concerns and controls] \\n\\nRCA Tools \\n[Root cause analysis tools selected and rationale] \\n\\nExpected Interim action \\n[Expected interim steps] \\n\\nCAPA \\n[Corrective and preventive actions]",
            
            "meeting_attendees": "3. Meeting Attendees \\n[List of all attendee names]",
            
            "impact_assessment": "4. Impact Assessment \\n[Detailed assessment of impact on product quality, patient safety, validation, regulatory compliance]",
            
            "criticality": "5. Criticality \\nCriticality: [Minor/Major/Critical] \\n[Rationale for criticality determination]"
        }}
        
        ## INSTRUCTIONS:
        1. Format each section exactly as shown in the template above
        2. Include all available information from the input data
        3. For any missing information, make reasonable assumptions based on pharmaceutical industry standards
        4. Ensure the report is comprehensive, professional, and follows regulatory expectations
        5. Include all five numbered sections with proper formatting
        6. Use the exact reference format shown in the example below
        
        ## EXAMPLE FORMAT REFERENCE:
        Follow this exact format for the report:

        1. Incident Title: Low Tablet Weights Identified During In-Process Checks on Tableting Line 5
           Deviation ID: [To be assigned]
           Date/Time of Occurrence: 19-Sep-2025, 15:00 hrs
           Location: Tableting Line 5
           Product: Analgesic (Over-the-Counter)
           Dosage Form: Tablets

        2. Background
           On 19-Sep-2025, 15:00 hrs during routine in-process checks on Tableting Line 5, low tablet weights were detected. The weights were below the specified limits. This deviation was identified by production operators during scheduled sampling.
           
           Personnel involved include Michael E. Saidi M. Rana S.
           
           Immediate Action
           Quarantined all tablets manufactured since the last acceptable in-process weight check. Halted further compression activity until investigation initiated. Secured equipment to prevent unintended use. Notified QA and initiated deviation record. Batch records and machine settings reviewed at line.
           
           Quality Concerns/Controls
           Product Quality Impact: Potential for sub-potent (ineffective) product reaching patients if not detected. Validation Impact: Question raised on validated status of equipment and process stability; possibility of drift in machine settings or inadequate process controls. Compliance Gaps: Need to verify adequacy of in-process check frequency, operator training, and equipment calibration/qualification status.
           
           RCA Tools
           Root Cause Analysis Due to potential major criticality the root cause tool selected is fishbone analysis.
           
           Expected Interim action
           Not discussed
           
           CAPA
           Not discussed.

        3. Meeting Attendees
           Michael E. Saidi M. Rana S.

        4. Impact Assessment
           Rationale: Deviation may impact product quality (low tablet weights → sub-potent dose) but no immediate patient safety risk as deviation was detected during in-process checks and impacted batch portion quarantined. Validation impact identified resulting in major criticality. Customer notification to be identified via QTA review.

        5. Criticality
           Criticality: Major
           
        IMPORTANT: Return ONLY valid JSON with the five requested sections. No explanations, no markdown code blocks, just the JSON object.
        """
    
    def modify_incident_report(self, input_data: ModifyIncidentReportRequest) -> FormalIncidentReport:
        prompt= f"""
        You are an expert AI assistant for pharmaceutical quality management and deviation reporting.
        Your task is to generate a formal incident report based on the transcription and any existing details provided.
        
        ## INPUT DATA:
        - Report: {input_data.report.json()}
        - Modifications needed: {input_data.modifications}
        
        
        ## OUTPUT FORMAT:
        Generate a structured incident report with the following 5 main sections. Your response must be a JSON object with these exact sections:
        
        {{
            "incident_title": "1. Incident Title [Title] \\nDeviation ID: [To be assigned] \\nDate/Time of Occurrence: [Date], [Time] hrs \\nLocation: [Location] \\nProduct: [Product Name] \\nDosage Form: [Form]",
            
            "background": "2. Background \\n[Detailed description of what happened] \\n\\nPersonnel involved include [list of names] \\n\\nImmediate Action \\n[Actions taken immediately after detection] \\n\\nQuality Concerns/Controls \\n[Quality concerns and controls] \\n\\nRCA Tools \\n[Root cause analysis tools selected and rationale] \\n\\nExpected Interim action \\n[Expected interim steps] \\n\\nCAPA \\n[Corrective and preventive actions]",
            
            "meeting_attendees": "3. Meeting Attendees \\n[List of all attendee names]",
            
            "impact_assessment": "4. Impact Assessment \\n[Detailed assessment of impact on product quality, patient safety, validation, regulatory compliance]",
            
            "criticality": "5. Criticality \\nCriticality: [Minor/Major/Critical] \\n[Rationale for criticality determination]"
        }}
        
        ## INSTRUCTIONS:
        1. Format each section exactly as shown in the template above
        2. Include all available information from the input data
        3. For any missing information, make reasonable assumptions based on pharmaceutical industry standards
        4. Ensure the report is comprehensive, professional, and follows regulatory expectations
        5. Include all five numbered sections with proper formatting
        6. Use the exact reference format shown in the example below
        
        ## EXAMPLE FORMAT REFERENCE:
        Follow this exact format for the report:

        1. Incident Title: Low Tablet Weights Identified During In-Process Checks on Tableting Line 5
           Deviation ID: [To be assigned]
           Date/Time of Occurrence: 19-Sep-2025, 15:00 hrs
           Location: Tableting Line 5
           Product: Analgesic (Over-the-Counter)
           Dosage Form: Tablets

        2. Background
           On 19-Sep-2025, 15:00 hrs during routine in-process checks on Tableting Line 5, low tablet weights were detected. The weights were below the specified limits. This deviation was identified by production operators during scheduled sampling.
           
           Personnel involved include Michael E. Saidi M. Rana S.
           
           Immediate Action
           Quarantined all tablets manufactured since the last acceptable in-process weight check. Halted further compression activity until investigation initiated. Secured equipment to prevent unintended use. Notified QA and initiated deviation record. Batch records and machine settings reviewed at line.
           
           Quality Concerns/Controls
           Product Quality Impact: Potential for sub-potent (ineffective) product reaching patients if not detected. Validation Impact: Question raised on validated status of equipment and process stability; possibility of drift in machine settings or inadequate process controls. Compliance Gaps: Need to verify adequacy of in-process check frequency, operator training, and equipment calibration/qualification status.
           
           RCA Tools
           Root Cause Analysis Due to potential major criticality the root cause tool selected is fishbone analysis.
           
           Expected Interim action
           Not discussed
           
           CAPA
           Not discussed.

        3. Meeting Attendees
           Michael E. Saidi M. Rana S.

        4. Impact Assessment
           Rationale: Deviation may impact product quality (low tablet weights → sub-potent dose) but no immediate patient safety risk as deviation was detected during in-process checks and impacted batch portion quarantined. Validation impact identified resulting in major criticality. Customer notification to be identified via QTA review.

        5. Criticality
           Criticality: Major
           
        IMPORTANT: Return ONLY valid JSON with the five requested sections. No explanations, no markdown code blocks, just the JSON object.
        """
        response = self.get_openai_response(prompt)
        
        try:
            report_sections = json.loads(response)
            
            formal_report = FormalIncidentReport(
                incident_title=IncidentReportSection(content=report_sections["incident_title"]),
                background=IncidentReportSection(content=report_sections["background"]),
                meeting_attendees=IncidentReportSection(content=report_sections["meeting_attendees"]),
                impact_assessment=IncidentReportSection(content=report_sections["impact_assessment"]),
                criticality=IncidentReportSection(content=report_sections["criticality"])
            )
            return formal_report
            
        except json.JSONDecodeError as e:
            print("Raw response:", response)
            raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON")
        except KeyError as e:
            print("Raw response:", response)
            raise HTTPException(status_code=500, detail=f"Missing required section in response: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating incident report: {str(e)}")

