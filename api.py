# api.py
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, ToolMessage

from mcp_tools import MCPToolkit
from langgraph_agent import create_agent
import config
import nest_asyncio

nest_asyncio.apply()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation du toolkit et de l'agent (sera reconnecté dans lifespan)
toolkit = MCPToolkit()
tools = toolkit.get_tools()
agent = create_agent(tools)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application FastAPI.

    - au startup : initialise et connecte le client MCP.
    - au shutdown : ferme proprement la connexion MCP.

    Args:
        app (FastAPI): instance de l'application.
    """
    # Startup
    try:
        await toolkit._get_client()
        logger.info("✅ MCP client connected")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MCP server: {e}")
        # L'API peut continuer, mais les appels échoueront
    yield
    # Shutdown
    await toolkit._close_client()
    logger.info("MCP client closed")


app = FastAPI(title="Industrial Agent API", lifespan=lifespan)

# CORS pour permettre l'accès depuis le frontend React (port 5173 par défaut)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: Optional[str] = None
    sql_query: Optional[str] = None
    results: Optional[Any] = None
    error: Optional[str] = None


@app.post("/ask", response_model=QuestionResponse)
async def ask(request: QuestionRequest):
    """Endpoint principal : reçoit une question en langage naturel et retourne la réponse de l'agent.

    Flux :
      1. Envoi la question au workflow agent.
      2. Analyse le dernier message pour en extraire la réponse textuelle.
      3. Extrait la requête SQL calculée (`execute_sql_query`) et le résultat des outils.
      4. Retourne un `QuestionResponse` structuré.

    Args:
        request (QuestionRequest): Objet de requête contenant `question`.

    Returns:
        QuestionResponse: Réponse formatée avec `answer`, `sql_query`, `results`, `error`.
    """
    try:
        # Appel de l'agent
        result = await agent.ainvoke({"messages": [HumanMessage(content=request.question)]})

        # Extraction robuste de la réponse finale
        last_msg = result["messages"][-1]

        if hasattr(last_msg, "content"):
            content = last_msg.content
            if isinstance(content, str):
                answer = content
            elif isinstance(content, list):
                # Gestion du format Gemini : liste de blocs
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        texts.append(block)
                    else:
                        texts.append(str(block))
                answer = "\n".join(texts)
            else:
                answer = str(content)
        else:
            answer = str(last_msg)

        # Sécurité supplémentaire : si answer est une liste ou un dict, le transformer en texte
        if isinstance(answer, (list, dict)) and answer:
            answer = str(answer)

        # Extraction de la dernière requête SQL et des résultats
        sql_query = None
        results = None
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc["name"] == "execute_sql_query":
                        sql_query = tc["args"]["query"]
            elif isinstance(msg, ToolMessage) and msg.content:
                try:
                    results = json.loads(msg.content)
                except json.JSONDecodeError:
                    results = msg.content

        return QuestionResponse(answer=answer, sql_query=sql_query, results=results)

    except Exception as e:
        logger.exception("Erreur dans l'agent")
        return QuestionResponse(error=str(e))