import os
import json
import openai
from fastapi import HTTPException
from dotenv import load_dotenv
from app.services.initiation.initiation_schema import PerMinuteInitiationRequest, PerMinuteInitiationResponse

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

                - {input_data.existing_incident_title}: (Optional) Previously extracted incident title, if any. If it exists, use it unless in transcription there is a specific mention; if not, generate a new one.
                - {input_data.transcribed_text}: The full transcript up to this point (latest cumulative 10-second update).
                - {input_data.existing_background_details}: (Optional) Previously extracted background details, if any.
                - {input_data.existing_background_attendee}: (Optional) List of previously known attendee names.
                - {input_data.existing_impact_assessment}: (Optional) Previously extracted impact assessment data, if any.

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

                Each of these three fields must be an dictionary object with:
                    - `"impact"`: "Yes" or "No"
                    - `"severity"`: One of "Low", "Medium", "High" if impact is "Yes", or "" if impact is "No".

                ✅ Examples:
                - "Product_Quality": {{ "impact": "Yes", "severity": "Medium" }}
                - "Patient_Safety": {{ "impact": "No", "severity": "" }}

                ---

                ### Instructions:

                1. Correct any transcription errors in `input.transcribed_text`.
                2. Use the full transcript to extract structured information.
                3. Incorporate previously extracted details (from `input.existing_background_details`, etc.) where applicable.
                4. If new information contradicts or improves prior data, update it.
                5. All keys must be present in the output structure.
                6. Respond ONLY with valid JSON — no markdown, no explanations, no code blocks.

                ---

                ### Example Input Object:

                {{
                "input": {{
                    "transcribed_text": "The team reviewed the updated templates and agreed that no immediate action was required.",
                    "existing_background_details": null,
                    "existing_background_attendee": ["Alice", "Bob"],
                    "existing_impact_assessment": null
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
                    }}
                }}
                }}
                """

                

    
    def get_openai_response (self, prompt:str)->str:
        completion =self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7            
        )
        return completion.choices[0].message.content




