from openai import OpenAI
from .base import BaseLLM
import base64
from io import BytesIO

class GPTClient(BaseLLM):

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_html(self, prompt, image):
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        response = self.client.chat.completions.create(
            model="gpt-4o",  # or "gpt-4-vision-preview" or "gpt-4o-mini"
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_b64}"
                        }
                    }
                ]
            }],
            max_tokens=4096
        )

        return response.choices[0].message.content.strip()