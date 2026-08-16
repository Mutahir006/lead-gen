"""
Vercel Python entrypoint. Vercel auto-detects this as a FastAPI app because
it finds `app = FastAPI()` and a matching requirements.txt at the project
root — no extra adapter needed.

Every route here just calls into the same lead_generator package the CLI
(main.py) uses. The pipeline logic doesn't know or care whether it was
triggered from a terminal or a web request.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lead_generator"))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import Response  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from graph.pipeline import run_pipeline  # noqa: E402
from db import fetch_leads, init_db  # noqa: E402
from export.csv_export import leads_to_csv_string  # noqa: E402

app = FastAPI(title="Rowentrix Lead Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your actual domain once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    city: str
    category: str
    country: str = "UK"
    max_results: int = 10  # keep this modest — see README on function timeouts
    no_website_only: bool = False


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        state = run_pipeline(
            city=req.city,
            category=req.category,
            country=req.country,
            max_results=req.max_results,
            no_website_only=req.no_website_only,
        )
        return {"leads": state["leads"], "log": state["log"]}
    except RuntimeError as e:
        # config errors (missing API keys etc.) — tell the caller plainly
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Pipeline failed: {e}")


@app.get("/api/leads")
def get_leads(min_score: int = 0):
    init_db()
    return {"leads": fetch_leads(min_score=min_score)}


@app.get("/api/export")
def export_csv(min_score: int = 0):
    csv_string = leads_to_csv_string(min_score=min_score)
    return Response(
        content=csv_string,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )
