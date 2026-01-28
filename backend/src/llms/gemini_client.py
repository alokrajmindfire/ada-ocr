import google.generativeai as genai
from .base import BaseLLM
from io import BytesIO
from config.logger import get_logger

logger = get_logger("gemini_client")


class GeminiClient(BaseLLM):

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel("gemini-3-flash-preview")
        logger.info("GeminiClient initialized")

    def generate_html_from_pdf(self, prompt, pdf_bytes):
        pdf_stream = BytesIO(pdf_bytes)

        response = self.model.generate_content([
            prompt,
            {
                "mime_type": "application/pdf",
                "data": pdf_stream.read()
            }
        ])

        texts = []
        for cand in response.candidates:
            for part in cand.content.parts:
                if hasattr(part, "text"):
                    texts.append(part.text)

        return "".join(texts), {"total_tokens": 0}
