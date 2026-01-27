from openai import OpenAI
from .base import BaseLLM
import base64
from io import BytesIO
from config.logger import get_logger

logger = get_logger("gpt_client")


# class GPTClient(BaseLLM):

#     def __init__(self, api_key: str):
#         self.client = OpenAI(api_key=api_key)
#         logger.info("GPTClient initialized")

#     def generate_html(self, prompt, image):
#         try:
#             logger.info("Converting image to base64")
#             buffer = BytesIO()
#             image.save(buffer, format="PNG")
#             img_b64 = base64.b64encode(buffer.getvalue()).decode()

#             logger.info("Sending request to OpenAI")
#             response = self.client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=[{
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": prompt},
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/png;base64,{img_b64}"
#                             }
#                         }
#                     ]
#                 }],
#                 max_tokens=4096
#             )

#             logger.info("OpenAI response received")
#             return response.choices[0].message.content.strip()

#         except Exception as e:
#             logger.exception("GPT HTML generation failed")
#             raise




class GPTClient(BaseLLM):

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        logger.info("GPTClient initialized")

    def generate_html(self, prompt, image):
        try:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode()

            response = self.client.responses.create(
                model="gpt-5.2",
                input=[{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{img_b64}"
                        }
                    ]
                }],
                max_output_tokens=16000
            )

            output = response.output_text.strip()

            usage = response.usage
            return output, {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens
            }

        except Exception:
            logger.exception("GPT HTML generation failed")
            raise
