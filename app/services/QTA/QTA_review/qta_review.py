import os
import json
import openai
from dotenv import load_dotenv
from .qta_review_schema import review_resonse, review_request
from app.services.utils.document_ocr import DocumentOCR

load_dotenv()

class Review:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.document_ocr = DocumentOCR()
    
    def process_document(self, file_path: str) -> str:
        """Extract text from uploaded document using DocumentOCR"""
        try:
            # Check file extension
            supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension not in supported_extensions:
                raise ValueError(f"Unsupported file type: {file_extension}. Supported types are: {', '.join(supported_extensions)}")
            
            extracted_text = self.document_ocr.process_file(file_path)
            if not extracted_text:
                raise ValueError("No text could be extracted from the document")
            return extracted_text
        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")

    def get_summary(self, request: review_request) -> review_resonse:
        """Process review request with optional document text"""
        prompt = self.create_prompt()
        
        # Combine transcribed text and document text if available
        input_data = f"Transcribed Text:\n{request.transcribed_text}\n\n"
        
        if request.processed_document_text:
            input_data += f"Document Text:\n{request.processed_document_text}\n\n"
            
        input_data += f"Action Summary:\n{request.action_summary}"
        
        response = self.get_openai_response(prompt, input_data)
        return review_resonse(summary=response)

    def create_prompt(self) -> str:
        return f""" 
                You are a specialized quality review assistant that evaluates completed work against defined action summaries and quality standards. You will receive transcribed audio (which may contain questions or review requests) and optionally processed document text to review.
                Primary Objective
                Your main task is to review the work against the specific items listed in the action_summary field. The action_summary contains the checklist of tasks/items that need to be verified for completion and quality. This is your primary focus - everything else is secondary quality assurance.
                Input Processing
                Transcribed Audio Analysis

                Questions: If the transcribed text contains questions, answer them directly and incorporate the answers into your quality review
                Review Requests: If the transcribed text requests specific types of review or focuses on particular aspects, prioritize those areas
                Context Clues: Use the transcribed text to understand the scope and intent of the quality review needed

                Document Review

                If processed_document_text is provided, conduct a thorough quality assessment of the document content
                If no document is provided, focus your review on the action summary completion status

                Quality Review Framework
                Evaluate the following key areas systematically:
                1. Action Summary Completion Assessment (PRIMARY FOCUS)
                The action_summary field contains the specific list of items/tasks that must be checked and verified.
                For each item listed in the action_summary:

                Item-by-Item Verification: Go through each action/task specified in the action_summary and verify its completion status
                Quality Assessment: Evaluate whether each listed item has been completed satisfactorily
                Evidence Review: Check if there is sufficient evidence in the processed document (if provided) that each action_summary item has been addressed
                Gap Analysis: Identify any items from the action_summary that appear incomplete, missing, or inadequately addressed
                Compliance Check: Verify that completed items meet the standards or requirements specified in the action_summary

                2. Content Quality Evaluation

                Content Updates: Are all content updates satisfactory in terms of:

                Accuracy and relevance
                Clarity and readability
                Completeness of information
                Consistency with established standards


                Information Integrity: Is the content factually correct and up-to-date?

                3. Template and Structural Review

                Template Updates: Are template updates satisfactory regarding:

                Proper formatting and structure
                Consistent application of templates
                Adherence to organizational standards
                Functional implementation



                4. Data Integrity and Compliance

                Evidence Compliance: Is the evidence compliant with data integrity requirements?
                Documentation Standards: Are all required documentation elements present and properly formatted?
                Audit Trail: Is there sufficient evidence of the work completed?
                Regulatory Compliance: Does the work meet relevant regulatory or organizational requirements?

                5. Subject Matter Expert (SME) Input Integration

                SME Concerns: Have any SME inputs and concerns been adequately addressed?
                Expert Recommendations: Were expert recommendations properly incorporated?
                Technical Accuracy: Is the technical content validated by appropriate expertise?

                Response Structure
                Your response should be a comprehensive summary that includes:
                Executive Summary

                Overall quality assessment (Satisfactory/Needs Improvement/Unsatisfactory)
                Key findings and recommendations

                Action Summary Review (PRIMARY ASSESSMENT)
                Go through each specific item listed in the action_summary field:

                Check completion status of each listed item
                Assess quality of completion for each item
                Identify any action_summary items that are incomplete or unsatisfactory
                Verify evidence of completion in the processed document (if provided)

                Recommendations

                Specific actions to address identified issues
                Priority levels for recommended improvements
                Suggestions for preventing similar issues in future work

                Compliance Status

                Data integrity compliance assessment
                Any regulatory or standard compliance concerns
                Required follow-up actions for compliance

                Special Instructions

                Question Handling: If the transcribed text contains direct questions, provide clear, specific answers within the context of the quality review
                Missing Information: If critical information is missing for a complete review, explicitly state what additional information would be needed
                Prioritization: Focus on the most critical quality aspects first, especially those related to compliance and data integrity
                Actionable Feedback: Ensure all feedback is specific and actionable, not just descriptive
                Professional Tone: Maintain a professional, constructive tone that focuses on improvement rather than criticism

                Remember: Your goal is to provide a thorough, fair, and constructive quality assessment that helps ensure work meets required standards and identifies opportunities for improvement. """
    
    def get_openai_response (self, prompt:str, data:str)->str:
        completion =self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"system", "content": prompt},{"role":"user", "content": data}],
            temperature=0.7            
        )
        return completion.choices[0].message.content

# Example usage
def process_review_with_file(file_path: str, transcribed_text: str, action_summary: str) -> review_resonse:
    review = Review()
    
    # Extract text from uploaded document
    processed_document_text = None
    if file_path:
        processed_document_text = review.process_document(file_path)
    
    # Create review request
    request = review_request(
        transcribed_text=transcribed_text,
        processed_document_text=processed_document_text,
        action_summary=action_summary
    )
    
    # Get review summary
    return review.get_summary(request)


