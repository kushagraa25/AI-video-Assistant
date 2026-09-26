import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI

# Load environment variables
load_dotenv()

DEFAULT_MODEL = os.getenv("MISTRAL_MODEL", "open-mistral-nemo")

def get_llm(temperature: float = 0.3, model_name: str | None = None) -> ChatMistralAI:
    """
    Returns a configured ChatMistralAI instance.
    Uses MISTRAL_MODEL from environment, defaulting to 'open-mistral-nemo'
    which is standard for free tier and standard Mistral accounts.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY is not set in environment or .env file. "
            "Please add your Mistral API key to the .env file."
        )

    chosen_model = model_name or os.getenv("MISTRAL_MODEL", DEFAULT_MODEL)

    return ChatMistralAI(
        model=chosen_model,
        mistral_api_key=api_key,
        temperature=temperature,
    )
