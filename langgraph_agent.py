import json
from typing import Annotated, Sequence, Optional, Dict, Any
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from llm_utils import get_langchain_llm
from decision_simulator import DecisionSimulator


class AgentState(dict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    results: Optional[Any] = None
    decision: Optional[Dict[str, Any]] = None
    sql_executed: bool = False
    loop_count: int = 0


def create_agent(tools, recursion_limit: int = 10):
    llm = get_langchain_llm()
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)
    simulator = DecisionSimulator()

    def call_model(state):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "simulate_decision"

    def simulate_decision_node(state):
        results = None
        sql_called = False
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage) and msg.name == "execute_sql_query":
                try:
                    results = json.loads(msg.content)
                    sql_called = True
                    if isinstance(results, dict) and "error" in results:
                        results = None
                except:
                    results = None
                break
        decision = simulator.simulate(results) if results else {
            "status": "no_data",
            "message": "Aucune donnée SQL valide à analyser.",
            "details": {},
            "requires_human_intervention": False
        }
        return {"results": results, "decision": decision, "sql_executed": sql_called}

    def check_sql_executed(state):
        loop_count = state.get("loop_count", 0) + 1
        state["loop_count"] = loop_count

        if not state.get("sql_executed") and state["decision"]["status"] == "no_data" and loop_count < 3:
            reminder = HumanMessage(
                content="Tu n'as pas encore exécuté de requête SQL. Utilise l'outil 'execute_sql_query' pour répondre à la question. "
                        "Assure-toi de bien construire la requête en fonction de la structure des tables que tu as décrites."
            )
            return {"messages": [reminder], "sql_executed": False, "loop_count": loop_count}
        return {}

    workflow = StateGraph(AgentState)

    workflow.add_node("model", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("simulate_decision", simulate_decision_node)
    workflow.add_node("check_sql", check_sql_executed)

    workflow.set_entry_point("model")
    workflow.add_conditional_edges("model", should_continue, {
        "tools": "tools",
        "simulate_decision": "simulate_decision"
    })
    workflow.add_edge("tools", "model")
    workflow.add_edge("simulate_decision", "check_sql")
    workflow.add_conditional_edges(
        "check_sql",
        lambda state: "model" if state.get("loop_count", 0) < 3 and not state.get("sql_executed") else END
    )

    return workflow.compile()