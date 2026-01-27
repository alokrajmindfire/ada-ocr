from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_PROVIDER: str = "gpt"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
