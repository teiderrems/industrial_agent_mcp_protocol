# langgraph_agent.py
from typing import Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from llm_utils import get_langchain_llm


class AgentState(dict):
    """État de l'agent utilisé par LangGraph.

    `messages` contient la séquence de messages échangés entre l'utilisateur,
    le modèle, et les outils. Le décorateur `add_messages` assure la sérialisation
    correcte et le suivi des messages à travers les transitions d'états.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]


def create_agent(tools, recursion_limit: int = 10):
    """Construit et compile un agent LangGraph via les outils fournis.

    L'agent fonctionne en boucle :
      1. Émet un appel modèle (`call_model`).
      2. Si le modèle a généré des `tool_calls`, exécute l'outil.
      3. Retourne au modèle (jusqu'à `recursion_limit`).

    Args:
        tools (list): Liste d'outils LangChain (`StructuredTool` ou équivalent).
        recursion_limit (int): Nombre maximal d'itérations pour éviter les boucles infinies.

    Returns:
        Callable: Workflow compilé avec `StateGraph` prêt à être invoqué (`ainvoke`).
    """
    llm = get_langchain_llm()
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    def call_model(state):
        """Étape du workflow qui appel le modèle avec les messages accumulés."""
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state):
        """Décide si l'agent doit exécuter un outil ou terminer.

        La condition est basée sur la présence de tool_calls dans le dernier message.
        """
        last_message = state["messages"][-1]
        # Si l'agent appelle des outils, on continue, sinon on termine
        return "tools" if last_message.tool_calls else END

    workflow = StateGraph(AgentState)
    workflow.add_node("model", call_model)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("model")
    workflow.add_conditional_edges("model", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "model")

    # Compile avec la limite de récursion (optionnel mais bien)
    return workflow.compile()