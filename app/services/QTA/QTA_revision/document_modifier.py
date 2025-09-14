import tempfile
import os
from pathlib import Path
from app.services.utils.process_file import FileProcessor
from app.services.utils.convert_file import FileConverter
import requests
from app.config.config import OPENAI_API_KEY

class DocumentModifierService:
    def __init__(self):
        self.file_processor = FileProcessor()
        self.file_converter = FileConverter()

    def modify_document(self, file_path, summary_text):
        # 1. Extract text from the file
        extracted_text = self.file_processor.process_file(file_path)
        if not extracted_text:
            raise Exception("Could not extract text from the uploaded file.")

        # 2. Use OpenAI API to modify the text according to the summary
        modified_text = self.modify_text_with_ai(extracted_text, summary_text)
        if not modified_text:
            raise Exception("AI did not return modified text.")

        # 3. Save the modified text to a temporary TXT file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as temp_txt:
            temp_txt.write(modified_text)
            temp_txt_path = temp_txt.name

        # 4. Convert the TXT file to PDF
        output_pdf_path = temp_txt_path.replace('.txt', '_modified.pdf')
        self.file_converter.txt_to_pdf(temp_txt_path, output_pdf_path)

        # 5. Clean up the temporary TXT file
        if os.path.exists(temp_txt_path):
            os.unlink(temp_txt_path)

        return output_pdf_path

    def modify_text_with_ai(self, original_text, summary_text):
        if not OPENAI_API_KEY:
            return None
        try:
            headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that edits documents based on user instructions."},
                    {"role": "user", "content": f"Here is the original document text:\n{original_text}\n\nPlease modify the document according to these instructions:\n{summary_text}\n\nReturn the full modified document text."}
                ],
                "max_tokens": 2048,
                "temperature": 0.3
            }
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                return None
        except Exception as e:
            return None
