import os
import json
import openai
from fastapi import HTTPException
from dotenv import load_dotenv
from .QTA_revision_schema import per_minute_qta_revision_request, per_minute_qta_revision_response, final_qta_revision_request, final_qta_revision_response
from app.services.utils.document_ocr import DocumentOCR
from pydantic import ValidationError


load_dotenv()

class QTARevision:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.document_ocr = DocumentOCR()
    


    def get_per_minute_summary(self, input_data: per_minute_qta_revision_request) -> per_minute_qta_revision_response:
        prompt = f"""
            You are a language model that receives an audio transcription related to quality and change processes.
            The transcription text is: {input_data.transcribed_text}

            You may also receive previous extracted information:
            - Existing changed details: {input_data.existing_changed_details}
            - Existing action summary: {input_data.existing_action_summary}

            Your task is to analyze the new transcription and update two sections:

            1. **changed_details** — List all topics discussed with brief explanations (1–2 sentences each).  
            Topics to detect:
                - Change Details (Upload change requests, Change control processes)
                - CAPA (Corrective and Preventive Actions)
                - SME (Subject Matter Expert) Inputs and Concerns
                - Gap Assessment (especially about in-house vs external templates)

            2. **action_summary** — Provide a concise list of concrete actions, next steps, or follow-up tasks mentioned in the audio.  
            Include actions required by CAPA, Change Control, or Change Requests.  
            If a gap assessment or document comparison is required, describe that as well.

            **Important Instructions:**
            - Always preserve and include any relevant content from the existing sections if still relevant.
            - If a topic was mentioned before but appears again, keep or update it as needed (do not remove unless explicitly contradicted).
            - Maintain markdown format for `changed_details` using `- **Topic**:` structure.
            - Write clear bullet points for `action_summary`.
            - Respond **only with valid JSON**, no markdown formatting outside the JSON and no explanations.

            Example Input:
            {{
            "text": "We discussed uploading the new change request and whether a gap assessment is required for external templates.",
            "existing_changed_details": "- **SME Inputs and Concerns**: SME raised issues about document alignment.",
            "existing_action_summary": "- Review SME feedback from last session."
            }}

            Example Output:
            {{
            "changed_details": "- **SME Inputs and Concerns**: SME raised issues about document alignment.\n- **Change Details**: The team discussed uploading a new change request.\n- **Gap Assessment**: A gap assessment may be required between in-house and external templates.",
            "action_summary": "- Upload the new change request for review.\n- Conduct gap assessment between internal and external templates.\n- Review SME feedback for document alignment."
            }}
        """




        

        
        response = self.get_openai_response(prompt)
        print(response)
        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
             raise HTTPException(status_code=500, detail="Failed to parse model response as JSON.")
        
        return per_minute_qta_revision_response(**response_dict)
    
    
    def get_final_summary(self, input_data:final_qta_revision_request) -> final_qta_revision_response:
        """Process review request with optional document text"""
        prompt = self.create_prompt(input_data)
        
        
        response = self.get_openai_response(prompt)
        print(response)
        response_dict = json.loads(response)
        return final_qta_revision_response(**response_dict)

    def create_prompt(self ,input_data: per_minute_qta_revision_request) -> str:
        return f"""
                You are an AI assistant responsible for revising a client document based on user-provided instructions and a modified version of the document.

                Your task involves the following steps:
                1. Analyze the **transcribed_text** to understand what changes the user is requesting.
                2. Compare the **client_document** with the **user_document** to identify modifications, additions, or deletions.
                3. Apply the necessary changes to the client_document to create a new version that reflects the user's input.

                After updating the document, return:
                - **action_summary**: A brief summary of the changes you made.
                - **change_details**: A categorized breakdown of changes (e.g., CAPA – Corrective and Preventive Actions, SME Inputs and Concerns, Gap Assessment).
                - **new_document_text**: The final revised version of the client document.

                ### User Instructions:
                {input_data.transcribed_text}

                ### Original Client Document:
                {input_data.client_document}

                ### Updated User Document (Reference for Changes):
                {input_data.user_document}

                Now, analyze and revise the client document accordingly. Return only the structured response in JSON format with keys: action_summary, change_details, and new_document_text.
                """
                
    def repeat_final_summary(
    self,
    existing_document: str,
    existing_action_summary: str,
    existing_change_details: dict,
    user_changes: str
) -> final_qta_revision_response:
        prompt = f"""
        You are an AI assistant tasked with revising a client document according to user-provided changes and an updated document.

        Instructions:
        1. Carefully analyze the user changes: {user_changes}
        2. Apply these changes to the existing document: {existing_document} to produce a revised document.
        3. Update the existing action summary: {existing_action_summary} and existing change details: {existing_change_details} based on the new revisions.

        Your response must be a single JSON object with the following keys:
        - "action_summary": A concise summary of all changes made.
        - "change_details": A detailed and categorized dictionary of changes (e.g., CAPA, SME Inputs and Concerns, Gap Assessment).
        - "new_document_text": The complete final revised client document text.

        IMPORTANT:
        - Return **ONLY** the JSON object, no explanations, no additional text.
        - Ensure the JSON is valid and properly formatted.

        Now, proceed with the analysis and revision, then respond with the JSON output only.
        """

        try:
            response_text = self.get_openai_response(prompt)

            parsed = json.loads(response_text)

            return final_qta_revision_response(
                action_summary=parsed["action_summary"],
                change_details=parsed["change_details"],
                new_document_text=parsed["new_document_text"]
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw response:\n{response_text}")
        except KeyError as e:
            raise ValueError(f"Missing expected key in LLM response: {e}")
        except ValidationError as e:
            raise ValueError(f"Response validation failed: {e}")
    
    def get_openai_response (self, prompt:str)->str:
        completion =self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7            
        )
        return completion.choices[0].message.content




