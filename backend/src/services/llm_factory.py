from llms.gemini_client import GeminiClient
from llms.gpt_client import GPTClient
from config.env import settings
from config.logger import get_logger

logger = get_logger("llm_factory")


def get_llm():
    logger.info(f"Initializing LLM provider: {settings.LLM_PROVIDER}")

    if settings.LLM_PROVIDER == "gemini":
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        logger.info("Using Gemini LLM")
        return GeminiClient(settings.GEMINI_API_KEY)

    if settings.LLM_PROVIDER == "gpt":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        logger.info("Using GPT LLM")
        return GPTClient(settings.OPENAI_API_KEY)

    logger.error(f"Invalid LLM_PROVIDER value: {settings.LLM_PROVIDER}")
    raise ValueError("Invalid LLM_PROVIDER")
