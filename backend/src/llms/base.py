from abc import ABC, abstractmethod
from PIL import Image

class BaseLLM(ABC):

    @abstractmethod
    def generate_html(self, prompt: str, image: Image.Image) -> str:
        pass
