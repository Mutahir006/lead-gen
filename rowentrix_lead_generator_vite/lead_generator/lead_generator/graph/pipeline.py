"""
The LangGraph workflow. This is the orchestration layer — each function below
is a NODE, and StateGraph wires them into a sequence of EDGES.

Why LangGraph here and not just a Python function calling other functions?
Two real reasons in this project:
  1. It gives you a visual/structural map of a multi-step pipeline that will
     keep growing (you'll likely add more nodes: dedupe, enrichment, retry
     logic, human-review-queue, etc.) — a graph scales better than nested ifs.
  2. The conditional edge below (skip AI-scoring node when not needed) is
     exactly the kind of stateful branching LangGraph is built for.

If this were staying at 3 fixed steps forever, honestly a plain Python
function would be simpler — don't take this as "always use LangGraph."
"""
from langgraph.graph import StateGraph, END

from config import Config
from graph.state import LeadGenState
from sources.osm_places import search_businesses, normalize_place
from detection.website_detector import detect_website_status, STATUS_NOT_FOUND
from detection.ai_tool_detector import detect_ai_tools_bulk
from scoring.lead_scorer import score_lead
from db import init_db, upsert_lead
from export.csv_export import export_to_csv

# Optional LLM note-writer, only imported/used if enabled
if Config.USE_LLM_SCORING:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=Config.OPENAI_API_KEY)


# ---------- NODES ----------
# Each node: takes the current state, returns a dict of the fields it changed.
# LangGraph merges that dict back into the state automatically.

def search_node(state: LeadGenState) -> dict:
    raw = search_businesses(state["city"], state["category"], state["country"], state["max_results"])
    normalized = [normalize_place(p, state["category"], state["city"]) for p in raw]
    return {
        "raw_places": normalized,
        "log": state["log"] + [f"search_node: found {len(normalized)} businesses"],
    }


def website_check_node(state: LeadGenState) -> dict:
    leads = []
    for place in state["raw_places"]:
        place["website_status"] = detect_website_status(place)
        leads.append(place)

    if state["no_website_only"]:
        leads = [l for l in leads if l["website_status"] == STATUS_NOT_FOUND]

    return {
        "leads": leads,
        "log": state["log"] + [f"website_check_node: {len(leads)} leads after filtering"],
    }


def ai_tool_node(state: LeadGenState) -> dict:
    # Concurrent, not sequential — required to fit inside Vercel's function
    # timeout (10s free tier / 60s Pro) once you're scanning 10-20 sites.
    leads = detect_ai_tools_bulk(state["leads"])
    return {"leads": leads, "log": state["log"] + ["ai_tool_node: scanned leads for existing AI tools (concurrent)"]}


def scoring_node(state: LeadGenState) -> dict:
    scored = [score_lead(lead) for lead in state["leads"]]

    if Config.USE_LLM_SCORING:
        for lead in scored:
            prompt = (
                f"Business: {lead['business_name']} ({lead['category']}) in {lead['city']}. "
                f"Website status: {lead['website_status']}. "
                f"AI tool status: {lead['ai_tool_status']}. "
                f"In one short sentence, note why this is or isn't a good prospect "
                f"for an AI automation agency selling voice agents and chatbots."
            )
            lead["llm_note"] = llm.invoke(prompt).content

    return {"leads": scored, "log": state["log"] + ["scoring_node: scored all leads"]}


def save_node(state: LeadGenState) -> dict:
    init_db()
    for lead in state["leads"]:
        upsert_lead(lead)
    return {"log": state["log"] + [f"save_node: saved {len(state['leads'])} leads to Postgres"]}


def export_node(state: LeadGenState) -> dict:
    path = export_to_csv()
    return {"log": state["log"] + [f"export_node: exported to {path}"]}


# ---------- CONDITIONAL EDGE ----------

def should_run_ai_detection(state: LeadGenState) -> str:
    """If there are zero leads after website filtering, skip straight to save."""
    return "ai_tool_node" if state["leads"] else "save_node"


# ---------- BUILD THE GRAPH ----------

def build_graph():
    graph = StateGraph(LeadGenState)

    graph.add_node("search_node", search_node)
    graph.add_node("website_check_node", website_check_node)
    graph.add_node("ai_tool_node", ai_tool_node)
    graph.add_node("scoring_node", scoring_node)
    graph.add_node("save_node", save_node)
    graph.add_node("export_node", export_node)

    graph.set_entry_point("search_node")
    graph.add_edge("search_node", "website_check_node")
    graph.add_conditional_edges(
        "website_check_node",
        should_run_ai_detection,
        {"ai_tool_node": "ai_tool_node", "save_node": "save_node"},
    )
    graph.add_edge("ai_tool_node", "scoring_node")
    graph.add_edge("scoring_node", "save_node")
    graph.add_edge("save_node", "export_node")
    graph.add_edge("export_node", END)

    return graph.compile()


def run_pipeline(city: str, category: str, country: str = "UK",
                  max_results: int = 20, no_website_only: bool = False) -> LeadGenState:
    Config.validate()
    app = build_graph()

    initial_state: LeadGenState = {
        "city": city,
        "category": category,
        "country": country,
        "max_results": max_results,
        "no_website_only": no_website_only,
        "raw_places": [],
        "leads": [],
        "log": [],
    }

    final_state = app.invoke(initial_state)
    return final_state
