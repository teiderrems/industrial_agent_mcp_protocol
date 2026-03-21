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


#     import config
# import logging
# from typing import List
# from pydantic import ConfigDict
# from langchain_core.language_models.chat_models import BaseChatModel
# from langchain_core.outputs import ChatResult

# logger = logging.getLogger(__name__)

# class FallbackChatModel(BaseChatModel):
#     _llms: List[BaseChatModel]
#     model_config = ConfigDict(extra="allow")

#     def __init__(self, llms: List[BaseChatModel], **kwargs):
#         super().__init__(**kwargs)
#         self._llms = llms

#     def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
#         for i, llm in enumerate(self._llms):
#             try:
#                 logger.info(f"Tentative avec LLM {i}...")
#                 return llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
#             except Exception as e:
#                 logger.warning(f"LLM {i} a échoué : {e}. Passage au suivant.")
#                 continue
#         raise Exception("Tous les LLMs configurés ont échoué.")

#     @property
#     def _llm_type(self) -> str:
#         return "fallback"

#     def bind_tools(self, tools, **kwargs):
#         bound_llms = [llm.bind_tools(tools, **kwargs) for llm in self._llms]
#         return FallbackChatModel(bound_llms)

# def get_langchain_llm():
#     """Crée un LLM avec fallback selon l'ordre défini dans LLM_ORDER."""
#     order = config.LLM_ORDER.split(",")
#     llms = []
#     for name in order:
#         name = name.strip().lower()
#         try:
#             if name == "gemini" and config.GEMINI_API_KEY:
#                 from langchain_google_genai import ChatGoogleGenerativeAI
#                 llms.append(ChatGoogleGenerativeAI(
#                     model=config.GEMINI_MODEL,
#                     google_api_key=config.GEMINI_API_KEY,
#                     temperature=0
#                 ))
#             elif name == "mistral" and config.MISTRAL_API_KEY:
#                 from langchain_mistralai import ChatMistralAI
#                 llms.append(ChatMistralAI(
#                     api_key=config.MISTRAL_API_KEY,
#                     model=config.MISTRAL_MODEL,
#                     temperature=0
#                 ))
#             # Ajoutez d'autres fournisseurs ici si besoin
#         except Exception as e:
#             logger.warning(f"Impossible d'initialiser {name} : {e}")

#     if not llms:
#         raise ValueError("Aucun LLM configuré. Vérifiez vos clés API ou activez USE_MOCK_LLM=true")
#     return FallbackChatModel(llms)