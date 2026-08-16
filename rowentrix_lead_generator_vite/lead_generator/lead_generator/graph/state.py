"""
The State that flows through every node in the LangGraph pipeline.
This is the ONE object every node reads from and writes back to.
"""
from typing import TypedDict, List, Optional


class LeadGenState(TypedDict):
    # inputs
    city: str
    category: str
    country: str
    max_results: int
    no_website_only: bool

    # working data, filled in by nodes as the graph runs
    raw_places: List[dict]
    leads: List[dict]

    # simple log so you can see what each node did, useful while learning
    log: List[str]
