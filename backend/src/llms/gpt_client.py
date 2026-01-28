from openai import OpenAI
import base64
from io import BytesIO
from config.logger import get_logger
from .base import BaseLLM

logger = get_logger("gpt_client")

class GPTClient(BaseLLM):

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        logger.info("GPTClient initialized")

    def generate_html_from_pdf(self, prompt: str, pdf_bytes: bytes):
        try:
            pdf_b64 = base64.b64encode(pdf_bytes).decode()

            response = self.client.responses.create(
                model="gpt-5.2",
                input=[{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_file",
                            "mime_type": "application/pdf",
                            "file_data": pdf_b64
                        }
                    ]
                }],
                max_output_tokens=20000
            )

            output_html = response.output_text.strip()
            usage = response.usage

            return output_html, {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens
            }

        except Exception:
            logger.exception("GPT PDF processing failed")
            raise
