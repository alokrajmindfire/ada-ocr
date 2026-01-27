import google.generativeai as genai
from .base import BaseLLM

class GeminiClient(BaseLLM):

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def generate_html(self, prompt, image):
        response = self.model.generate_content([prompt, image])

        texts = []
        for cand in response.candidates:
            if not cand.content:
                continue
            for part in cand.content.parts:
                if hasattr(part, "text"):
                    texts.append(part.text)

        return "".join(texts).replace("```html", "").replace("```", "").strip()
