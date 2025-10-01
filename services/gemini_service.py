import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("GeminiService initialized.")

    def summarize_symptoms(self, symptoms: str, known_allergies: str = None, current_medication: str = None, medical_history: str = None, additional_note: str = None) -> str:
        prompt = (
            "You are a helpful medical assistant. Summarize the following patient information "
            "into a concise, one or two-sentence note for a doctor. Focus on the key complaints, "
            "duration, severity, and relevant medical details such as allergies, medications, "
            "medical history, and any additional notes provided.\n\n"
            f"Patient Symptoms: \"{symptoms}\"\n"
            f"Known Allergies: \"{known_allergies or 'None provided'}\"\n"
            f"Current Medication: \"{current_medication or 'None provided'}\"\n"
            f"Medical History: \"{medical_history or 'None provided'}\"\n"
            f"Additional Notes: \"{additional_note or 'None provided'}\"\n\n"
            "Summary:"
        )

        try:
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            logger.info(f"Successfully generated summary for symptoms: {symptoms[:50]}...")
            return summary
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            # Fallback in case of API error
            return "Could not generate summary. Please review patient information manually."