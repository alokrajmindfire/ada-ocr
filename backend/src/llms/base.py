from abc import ABC, abstractmethod

class BaseLLM(ABC):

    @abstractmethod
    def generate_html_from_pdf(self, prompt: str, pdf_bytes: bytes):
        pass
