import google.generativeai as genai
from .base import BaseLLM
from io import BytesIO
from config.logger import get_logger

logger = get_logger("gemini_client")


class GeminiClient(BaseLLM):

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("GeminiClient initialized")

    def generate_html(self, prompt, image):
        """
        Generate HTML from a text prompt and a PIL.Image using Gemini.
        Returns (html_output, usage_info).
        """
        try:
            # Resize image to reduce timeout risk
            max_width = 1024
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height))

            # Generate content with prompt + image
            response = self.model.generate_content([prompt, image])
            # usage = getattr(response, "usage_metadata", None)
            # if usage:
            #     logger.info("\nToken usage details from response:")
            #     logger.info(f"Prompt tokens: {usage.prompt_token_count}")
            #     logger.info(f"Output tokens: {usage.candidates_token_count}")
            #     logger.info(f"Total tokens: {usage.total_token_count}")
            # Extract text safely
            texts = []
            for cand in response.candidates:
                if not cand.content:
                    continue
                # Correct: cand.content.parts is iterable
                for part in cand.content.parts:
                    if hasattr(part, "text"):
                        texts.append(part.text)

            output = "".join(texts).replace("```html", "").replace("```", "").strip()

            # Dummy usage info for compatibility
            usage_info = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }

            logger.info("Gemini HTML generation successful")
            return output, usage_info

        except Exception as e:
            logger.exception(f"Gemini HTML generation failed: {str(e)}")
            raise
