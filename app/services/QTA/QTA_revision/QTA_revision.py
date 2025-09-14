import openai
import os
import tempfile
from typing import Dict, List
from fastapi import UploadFile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceRevisionService:
    def __init__(self):
        """Initialize the voice revision service with OpenAI API"""
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    async def process_voice_file(self, audio_file: UploadFile) -> Dict:
        """
        Process uploaded audio file and return transcribed text with summary
        
        Args:
            audio_file: Uploaded audio file
            
        Returns:
            Dict containing transcribed_text, bullet_points, and summary
        """
        try:
            # Step 1: Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.filename.split('.')[-1]}") as tmp_file:
                content = await audio_file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Step 2: Transcribe audio using OpenAI Whisper
            transcribed_text = await self._transcribe_audio(tmp_file_path)
            
            # Step 3: Convert to bullet points
            bullet_points = await self._convert_to_bullet_points(transcribed_text)
            
            # Step 4: Generate summary
            summary = await self._generate_summary(bullet_points)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            return {
                "transcribed_text": transcribed_text,
                "bullet_points": bullet_points,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error processing voice file: {str(e)}")
            # Clean up temp file if exists
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            raise e
    
    async def _transcribe_audio(self, file_path: str) -> str:
        """
        Transcribe audio file using OpenAI Whisper API
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        try:
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            logger.info("Audio transcription completed successfully")
            return transcript
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise e
    
    async def _convert_to_bullet_points(self, text: str) -> List[str]:
        """
        Convert transcribed text into structured bullet points
        
        Args:
            text: Raw transcribed text
            
        Returns:
            List of bullet points
        """
        try:
            prompt = f"""
            Convert the following transcribed text into clear, organized bullet points. 
            Focus on extracting key information, instructions, or requirements mentioned in the text.
            Make each bullet point concise and actionable.
            
            Text: {text}
            
            Return only the bullet points, one per line, starting with "•".
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that organizes text into clear bullet points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            bullet_text = response.choices[0].message.content.strip()
            bullet_points = [point.strip() for point in bullet_text.split('\n') if point.strip() and point.strip().startswith('•')]
            
            logger.info(f"Generated {len(bullet_points)} bullet points")
            return bullet_points
            
        except Exception as e:
            logger.error(f"Error converting to bullet points: {str(e)}")
            raise e
    
    async def _generate_summary(self, bullet_points: List[str]) -> str:
        """
        Generate a concise summary from bullet points
        
        Args:
            bullet_points: List of bullet points
            
        Returns:
            Summary text
        """
        try:
            bullet_text = '\n'.join(bullet_points)
            
            prompt = f"""
            Based on the following bullet points, create a concise summary that captures the main themes and key requirements.
            The summary should be 2-3 sentences long and highlight the most important points.
            
            Bullet Points:
            {bullet_text}
            
            Provide a clear, actionable summary.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries from bullet points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            summary = response.choices[0].message.content.strip()
            
            logger.info("Summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise e