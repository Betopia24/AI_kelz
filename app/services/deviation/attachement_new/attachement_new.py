import os
import json
import openai
from fastapi import HTTPException
from dotenv import load_dotenv
from app.services.deviation.attachement_new.attachement_new_schema import AttachementRequest, AttachementResponse


load_dotenv()

class AttachementTitle:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    

    def change_file_titles(self, input_data: AttachementRequest) -> AttachementResponse:
        import json
        

        prompt= self.create_prompt(input_data)
        response = self.get_openai_response(prompt).strip()
        print("Raw model response:", response)

        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError as e:
            print("Model response:", response)
            raise HTTPException(status_code=500, detail="Failed to parse model response as JSON.")

        return AttachementResponse(**response_dict)

    def create_prompt(self, input_data: AttachementResponse) -> str:
        return  f"""
                
                """

                

    
    def get_openai_response (self, prompt:str)->str:
        completion =self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7            
        )
        return completion.choices[0].message.content



