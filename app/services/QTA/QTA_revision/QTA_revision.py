import os
import json
import openai
from fastapi import HTTPException
from dotenv import load_dotenv
from .QTA_revision_schema import per_minute_qta_revision_request, per_minute_qta_revision_response, final_qta_revision_request, final_qta_revision_response, repeat_qta_revision_request
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
            - Existing changed details: {input_data.changed_details}
            - Existing action summary: {input_data.action_summary}

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
        try:
            system_prompt = self.create_system_prompt()
            user_prompt = self.create_user_prompt(input_data)
            response = self.get_openai_response(user_prompt, system_prompt)
            print(f"OpenAI Response: {response}")
            
            if not response or response.strip() == "":
                raise ValueError("Empty response from OpenAI")
            
            response_dict = json.loads(response)
            return final_qta_revision_response(**response_dict)
        
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse OpenAI response as JSON: {str(e)}")
        except ValidationError as e:
            raise HTTPException(status_code=500, detail=f"Response validation failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in get_final_summary: {str(e)}")

    def create_system_prompt(self) -> str:
        return """You are an AI assistant specialized in QTA (Quality Technical Agreement) document revision.

Your role and capabilities:
- Expert in quality management documents including SOPs, CAPA, SME reviews, Contracts and compliance requirements
- Skilled in document structure analysis and professional formatting
- Focused on maintaining regulatory compliance and quality standards

Your task process:
1. Analyze user instructions to understand exactly what changes are requested
2. Examine all provided documents to understand their content and relationships
3. Apply requested changes to create revised versions of documents
4. Ensure all revisions maintain professional structure and formatting
5. Focus on quality-related aspects like SOPs, CAPA, SME inputs, and compliance requirements

Response requirements:
- Return ONLY valid JSON with exactly three keys: "action_summary", "change_details", "document_text"
- "action_summary": Brief summary of changes made to which documents
- "change_details": Detailed breakdown using markdown formatting with categories like Document Structure Changes, Content Additions/Modifications, Safety and Compliance Updates, Process Improvements
- "document_text": Complete final revised document content (never abbreviated)
- "change_details" must be a single string with \\n for line breaks, not an object or array
- Maintain document formatting and structure in the final output
- If multiple documents are revised, combine them appropriately in document_text

Critical formatting rules:
- Document filenames are dynamic - analyze content to understand what each document contains  
- Include complete revised document text, never use placeholders like "[...]" or "Content continues..."
- Preserve original document structure, numbering, and professional formatting"""
                
                

    def create_user_prompt(self, input_data: final_qta_revision_request) -> str:
        return f"""Please revise the following documents according to the user instructions.

                    User Instructions:
                    {input_data.transcribed_text}

                    Available Documents:
                    {input_data.documents}

                    Provide your response as a JSON object with the three required keys."""
                
                
    def repeat_final_summary(
    self,
    input_data: repeat_qta_revision_request
) -> final_qta_revision_response:
        prompt = f"""
        You are an AI assistant tasked with revising a client document according to user-provided changes and an updated document.

        Instructions:
        1. Carefully analyze the user changes: {input_data.transcribed_text}
        2. Apply these changes to the existing document: {input_data.document_text} to produce a revised document.
        3. Update the existing action summary: {input_data.action_summary} and existing change details: {input_data.change_details} based on the new revisions.

        Your response must be a single JSON object with the following keys:
        - "action_summary": A concise summary of all changes made (as a string).
        - "change_details": A detailed string of changes using markdown formatting. Use bullet points to organize categories (e.g., CAPA, SME Inputs and Concerns, Gap Assessment). This must be a single string, not an object or array.
        - "document_text": The complete final revised client document text (as a string).

        **IMPORTANT**:
        - Return **ONLY** the JSON object, no explanations, no additional text.
        - Ensure the JSON is valid and properly formatted.
        - The "change_details" field must be a STRING with markdown formatting, not an object or array.

        Example format:
        {{
          "action_summary": "Updated contract terms...",
          "change_details": "- **Category 1**: Description of changes\\n- **Category 2**: More changes\\n- **Category 3**: Additional modifications",
          "document_text": "Complete document text here..."
        }}

        Now, proceed with the analysis and revision, then respond with the JSON output only.
        """

        try:
            response_text = self.get_openai_response(prompt)

            parsed = json.loads(response_text)

            return final_qta_revision_response(
                action_summary=parsed["action_summary"],
                change_details=parsed["change_details"],
                document_text=parsed["document_text"]
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw response:\n{response_text}")
        except KeyError as e:
            raise ValueError(f"Missing expected key in LLM response: {e}")
        except ValidationError as e:
            raise ValueError(f"Response validation failed: {e}")
    
    def get_openai_response(self, prompt: str, system_prompt: str = None) -> str:
        try:
            print(f"Sending request to OpenAI with model: gpt-4")
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7            
            )
            
            response_content = completion.choices[0].message.content
            print(f"Received response length: {len(response_content) if response_content else 0}")
            
            if not response_content:
                raise ValueError("OpenAI returned empty response")
                
            return response_content
            
        except Exception as e:
            print(f"Error in OpenAI API call: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")




