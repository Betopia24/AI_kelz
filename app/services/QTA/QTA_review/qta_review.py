import os
import json
import openai
from fastapi import HTTPException
from dotenv import load_dotenv
from .qta_review_schema import per_minute_qta_review_request, per_minute_qta_review_response, final_qta_review_request, final_qta_review_response
from app.services.utils.document_ocr import DocumentOCR

load_dotenv()

class QTAreview:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.document_ocr = DocumentOCR()
    


    def get_per_minute_summary(self, input_data: per_minute_qta_review_request) -> per_minute_qta_review_response:
        import json

        transcribed_text = json.dumps(input_data.transcribed_text)
        existing_quality_review = json.dumps(input_data.existing_quality_review or "")

        prompt = f"""
                You are a language model that receives audio transcriptions {transcribed_text} related to quality and change processes. Your task is to analyze the transcription and determine whether any of the following quality review aspects are discussed. You should also correct any transcription errors.

                Quality Review Criteria to Analyze:

                • Have list of actions in action summary been completed satisfactorily?  
                • Are content updates satisfactory?  
                • Are template updates satisfactory?  
                • Is the evidence compliant with data integrity?  
                • SME Inputs and Concerns

                You may also receive existing details from earlier transcriptions {existing_quality_review}. If an item was already covered previously, you must still include it in your response if it is present in the new transcription.

                Instructions:

                1. Fix any transcription errors in the input.  
                2. Return the corrected transcription under `user_msg`.  
                3. Identify and list all relevant quality review aspects covered in the transcription under `changed_details`, along with 1–2 sentences for each explaining what was said.  
                4. Include both new and previously covered relevant details, preserving the markdown format.  
                5. Respond ONLY with valid JSON, no markdown, no explanations.  
                6. Your output must follow the structure below:

                Example Input:

                {{
                "transcribed_text": "We reviewed the updated templates and the content looked good overall.",
                "existing_quality_review": "- **SME Inputs and Concerns**: SME raised a concern about the clarity of one section."
                }}

                Example Output:

                {{
                "quality_review": "- **SME Inputs and Concerns**: SME raised a concern about the clarity of one section.\\n- **Are content updates satisfactory?**: The team reviewed the updated content and found it satisfactory.\\n- **Are template updates satisfactory?**: The updated templates were reviewed and found to be acceptable."
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

    def create_prompt(self, input_data: per_minute_qta_review_request) -> final_qta_review_response:
        return f"""
                You are an AI assistant responsible for updating a client document.

                Your task is to revise the **original_document** using:
                1. The user's spoken instructions provided in the **transcribed_text**.
                2. The **reference_document**, which includes content on a similar topic but is a good example of how the document should be.

                ### Instructions:
                - First, analyze the **transcribed_text** to extract key instructions or intent behind the changes.
                - Then, compare the **original_document** with the **reference_document** to identify edits such as additions, removals, or rewritten sections.
                - Use both sources (transcription and reference) to make accurate and complete updates to the **original_document**.

                Your response must be a valid JSON object with the following fields:

                - **quality_review**: A review of quality-related aspects (e.g., Are actions completed? Are content and template updates satisfactory? Is evidence compliant with data integrity? Are SME concerns addressed?).
                - **change_summary**: A categorized summary of changes made (e.g., SME Inputs and Concerns, CAPA, Gap Assessment, etc.).
                - **review_summary**: A brief evaluation of how well the updates align with the user's spoken instructions and the reference document.
                - **new_document_text**: The full revised version of the original document, reflecting all relevant changes.

                ### Transcribed Text (User Instructions):
                {input_data.transcribed_text}

                ### Reference Document (With Intended Changes):
                {input_data.reference_document}

                ### Original Document (To Be Updated):
                {input_data.original_document}

                Generate the updated document and return the full response as a structured JSON object.
                """

                
    def repeat_final_summary(existing_document, existing_quality_review, existing_change_summary, exists_review_summary,user_changes) -> final_qta_review_response:
        prompt = f"""
        You are an AI assistant tasked with revising a client document based on user-provided feedback.

        ### Instructions:
        1. Carefully review the user changes below and interpret the intended modifications:
        {user_changes}

        2. Apply these changes to the existing document:
        {existing_document}

        3. Based on the applied updates, revise the following summaries as needed:
        - Existing Quality Review: {existing_quality_review}
        - Existing Change Summary: {existing_change_summary}
        - Existing Review Summary: {exists_review_summary}

        ### Response Format:
        Return a valid JSON object with the following fields:
        - "quality_review": Updated quality-related feedback (e.g., template/content updates, data integrity, SME concerns, etc.)
        - "change_summary": A categorized summary of the changes made.
        - "review_summary": A brief evaluation of how the new changes align with the document’s intent.
        - "new_document_text": The fully revised client document incorporating the user changes.

        ### Important:
        - Return **only** the JSON object. No explanations or extra text.
        - Make sure the JSON is well-formatted and valid.

        Begin processing now and return only the final JSON output.
        """
        return prompt

    
    def get_openai_response (self, prompt:str)->str:
        completion =self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7            
        )
        return completion.choices[0].message.content




