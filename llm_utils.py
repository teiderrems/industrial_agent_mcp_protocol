# llm_utils.py
import config

def get_langchain_llm():
    order = config.LLM_ORDER.split(",")
    for name in order:
        name = name.strip().lower()
        if name == "gemini" and config.GEMINI_API_KEY:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=config.GEMINI_MODEL,
                google_api_key=config.GEMINI_API_KEY,
                temperature=0
            )
        elif name == "mistral" and config.MISTRAL_API_KEY:
            from langchain_mistralai import ChatMistralAI
            return ChatMistralAI(
                api_key=config.MISTRAL_API_KEY,
                model=config.MISTRAL_MODEL,
                temperature=0
            )
    raise ValueError("Aucun LLM valide configuré. Vérifiez vos clés API ou activez USE_MOCK_LLM=true")