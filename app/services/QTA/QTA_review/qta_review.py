import os
import json
import openai
from fastapi import HTTPException
from dotenv import load_dotenv
from .qta_review_schema import per_minute_qta_review_request, per_minute_qta_review_response, final_qta_review_request, final_qta_review_response, repeat_qta_review_request
from app.services.utils.document_ocr import DocumentOCR

load_dotenv()

class QTAreview:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.document_ocr = DocumentOCR()
    


    def get_per_minute_summary(self, input_data: per_minute_qta_review_request) -> per_minute_qta_review_response:
        import json

        transcribed_text = json.dumps(input_data.transcribed_text)
        existing_quality_review = json.dumps(input_data.quality_review or [])

        prompt = f"""
                You are a language model that receives audio transcript {transcribed_text} related to quality and change processes. Your task is to analyze the text and determine whether any of the following quality review aspects are discussed.

                You may also receive existing details from earlier reviews {existing_quality_review}. If an item was already covered previously, you must still include it in your response if it is present in the new text.

                **Change Summary**: Provide detailed summary of actions to be completed by AI on attachment or new documents as required auto transcription.

                **Review Summary**: Observations and findings (e.g., "Temperature excursion in storage area. Product stored above acceptable limits").

                Quality Review Criteria to Analyze:
                • Have list of actions in action summary been completed satisfactorily?  
                • Are content updates satisfactory?  
                • Are template updates satisfactory?  
                • Is the evidence compliant with data integrity?  
                • SME Inputs and Concerns

                Instructions:
                1. Analyze the transcript and update the quality_review, change_summary, and review_summary based on the content.
                2. Include both new and previously covered relevant details, preserving existing information.
                3. Respond ONLY with valid JSON, no markdown, no explanations.
                4. Your output must follow the structure below:

                {{
                "quality_review": [
                  {{"criterion": "Actions Completed", "assessment": "Description of completion status"}},
                  {{"criterion": "Content Updates", "assessment": "Assessment of content updates"}},
                  {{"criterion": "Template Updates", "assessment": "Assessment of template updates"}}
                ],
                "change_summary": "Single string with detailed summary of actions to be completed by AI on attachment or new documents",
                "review_summary": "Single string with observations and findings from the review"
                }}
                """

        response = self.get_openai_response(prompt).strip()

        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError as e:
            print("Model response:", response)
            raise HTTPException(status_code=500, detail="Failed to parse model response as JSON.")

        return per_minute_qta_review_response(**response_dict)

    
    def get_final_summary(self, input_data:final_qta_review_request) -> final_qta_review_response:
        """Process review request with optional document text"""
        prompt = self.create_prompt(input_data)
        
        
        response = self.get_openai_response(prompt)
        print(response)
        response_dict = json.loads(response)
        return final_qta_review_response(**response_dict)

    def create_prompt(self, input_data: final_qta_review_request) -> str:
        return f"""
                You are an AI assistant responsible for updating a client document.

                Your task is to revise the **original_document** using:
                1. The user's instructions provided in the **transcribed_text**.
                2. The **reference_document**, which includes content on a similar topic but is a good example of how the document should be.

                ### Instructions:
                - First, analyze the **transcribed_text** to extract key instructions or intent behind the changes.
                - Then, compare the **original_document** with the **reference_document** to identify edits such as additions, removals, or rewritten sections.
                - Use both sources (instructions and reference) to make accurate and complete updates to the **original_document**.

                Your response must be a valid JSON object with the following fields:

                - **quality_review**: A list of objects with criterion and assessment (e.g., [{{"criterion": "Actions Completed", "assessment": "All actions satisfactorily completed"}}, {{"criterion": "Content Updates", "assessment": "Content updates are satisfactory"}}, {{"criterion": "Data Integrity", "assessment": "Evidence compliant with data integrity standards"}}]).
                - **change_summary**: A single string with detailed summary of actions to be completed by AI on attachment or new documents as required auto transcription.
                - **review_summary**: A single string with observations and findings from the review (e.g., "Temperature excursion in storage area. Product stored above acceptable limits").
                - **document_text**: The full revised version of the original document, reflecting all relevant changes.

                **CRITICAL**: 
                - quality_review must be a list of objects (not strings)
                - change_summary must be a single string (not an array)
                - review_summary must be a single string (not an array)

                ### User Instructions:
                {input_data.transcribed_text}

                ### Reference Document (With Intended Changes):
                {input_data.reference_document}

                ### Original Document (To Be Updated):
                {input_data.original_document}

                Generate the updated document and return the full response as a structured JSON object.

                Example format:
                {{
                  "quality_review": [
                    {{"criterion": "Actions Completed", "assessment": "All user instructions have been addressed"}},
                    {{"criterion": "Content Updates", "assessment": "Content updates are satisfactory"}},
                    {{"criterion": "Template Updates", "assessment": "Template structure improved"}}
                  ],
                  "change_summary": "Single string describing actions completed on documents",
                  "review_summary": "Single string with observations and findings",
                  "document_text": "Full updated document text here..."
                }}
                """

                
    def repeat_final_summary(self, input_data: repeat_qta_review_request) -> final_qta_review_response:
        prompt = f"""
        You are an AI assistant tasked with revising a client document based on user-provided feedback.

        ### Instructions:
        1. Carefully review the user changes below and interpret the intended modifications:
        {input_data.transcribed_text}

        2. Apply these changes to the existing document:
        {input_data.document}

        3. Based on the applied updates, revise the following summaries as needed:
        - Existing Quality Review: {input_data.quality_review}
        - Existing Change Summary: {input_data.change_summary}
        - Existing Review Summary: {input_data.review_summary}

        ### Response Format:
        Return a valid JSON object with the following fields:
        - "quality_review": List of objects, each with "criterion" and "assessment" fields
        - "change_summary": Single string with detailed summary of actions to be completed by AI on attachment or new documents as required auto transcription
        - "review_summary": Single string with observations and findings from the review (e.g., "Temperature excursion in storage area. Product stored above acceptable limits")
        - "document_text": The fully revised client document incorporating the user changes

        Example format:
        {{
          "quality_review": [
            {{"criterion": "Actions Completed", "assessment": "All user instructions have been addressed"}},
            {{"criterion": "Content Updates", "assessment": "Content updates are satisfactory"}},
            {{"criterion": "Template Updates", "assessment": "Template structure improved"}}
          ],
          "change_summary": "Single string describing actions completed on documents",
          "review_summary": "Single string with observations and findings",
          "document_text": "Full updated document text here..."
        }}

        ### Important:
        - Return **only** the JSON object. No explanations or extra text.
        - Make sure the JSON is well-formatted and valid.

        Begin processing now and return only the final JSON output.
        """
        
        try:
            response_text = self.get_openai_response(prompt)
            parsed = json.loads(response_text)
            return final_qta_review_response(**parsed)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw response:\n{response_text}")
        except Exception as e:
            raise ValueError(f"Error in repeat final summary: {e}")

    
    def get_openai_response (self, prompt:str)->str:
        completion =self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7            
        )
        return completion.choices[0].message.content




