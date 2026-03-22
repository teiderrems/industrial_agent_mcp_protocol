import json
import logging
import io  # <-- moved to top
import math
from collections import deque
from contextlib import asynccontextmanager
from typing import Optional, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from PIL import Image, ImageDraw, ImageFont

from mcp_tools import MCPToolkit
from langgraph_agent import create_agent
import config
import nest_asyncio

nest_asyncio.apply()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation du toolkit et de l'agent
toolkit = MCPToolkit()
tools = toolkit.get_tools()
agent = create_agent(tools)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await toolkit._get_client()
        logger.info("✅ MCP client connected")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MCP server: {e}")
    yield
    await toolkit._close_client()
    logger.info("MCP client closed")


app = FastAPI(title="Industrial Agent API", lifespan=lifespan)

# CORS
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
    decision: Optional[dict] = None
    requires_human_intervention: Optional[bool] = False

# ---------- API endpoints ----------
@app.post("/ask", response_model=QuestionResponse)
async def ask(request: QuestionRequest):
    try:
        system_prompt = """Tu es un agent SQL expert. Tu dois répondre aux questions des utilisateurs en interrogeant la base de données.

**Règles strictes :**
1. Utilise l'outil 'list_tables' pour connaître les tables disponibles.
2. Utilise l'outil 'describe_table' pour connaître la structure des tables pertinentes.
3. **IMPÉRATIF** : Après avoir compris la structure, tu DOIS utiliser l'outil 'execute_sql_query' pour exécuter une requête SQL SELECT qui répond directement à la question.
   - Par exemple, si on demande "Quelle est la température moyenne des machines ?", tu dois exécuter : SELECT AVG(temperature) FROM machines.
4. Enfin, fournis une réponse en langage naturel basée sur les résultats de la requête.

N'oublie jamais d'exécuter une requête SQL. Pour les questions de données (température, temps d'arrêt, etc.), l'exécution SQL est obligatoire.
"""
        initial_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.question)
        ]
        result = await agent.ainvoke({"messages": initial_messages})

        # Extract answer
        last_msg = result["messages"][-1]
        if hasattr(last_msg, "content"):
            content = last_msg.content
            if isinstance(content, str):
                answer = content
            elif isinstance(content, list):
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

        if isinstance(answer, (list, dict)) and answer:
            answer = str(answer)

        # Extract SQL and results
        sql_query = None
        results = None
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc["name"] == "execute_sql_query":
                        sql_query = tc["args"]["query"]
            elif isinstance(msg, ToolMessage) and msg.name == "execute_sql_query" and msg.content:
                try:
                    results = json.loads(msg.content)
                except json.JSONDecodeError:
                    results = msg.content

        # Extract decision
        decision = result.get("decision")
        requires_human_intervention = result.get("requires_human_intervention", False)

        return QuestionResponse(
            answer=answer,
            sql_query=sql_query,
            results=results,
            decision=decision,
            requires_human_intervention=requires_human_intervention
        )

    except Exception as e:
        logger.exception("Erreur dans l'agent")
        return QuestionResponse(error=str(e))


@app.get("/api/workflow/graph.png")
async def get_workflow_graph_image():
    """Return a PNG image of the LangGraph workflow."""
    try:
        # Get the compiled agent's graph and render as PNG bytes
        img_bytes = agent.get_graph().draw_mermaid_png()
        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        logger.error(f"Graph image generation error: {e}", exc_info=True)
        return Response(content=b"Error generating graph", status_code=500)