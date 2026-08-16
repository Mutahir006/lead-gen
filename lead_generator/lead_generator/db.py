"""
Postgres storage layer (works with Supabase, Neon, Vercel Postgres — anything
that gives you a standard connection string). Switched from SQLite because
Vercel's serverless functions have an ephemeral filesystem: a SQLite file
written during one request is gone by the next request. Postgres is the
correct fix, not a workaround.
"""
import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL")

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    business_name TEXT NOT NULL,
    category TEXT,
    address TEXT,
    city TEXT,
    postcode TEXT,
    website TEXT,
    phone TEXT,
    website_status TEXT,
    ai_tool_status TEXT,
    ai_tool_vendor TEXT,
    lead_score INTEGER,
    lead_status TEXT,
    source TEXT,
    place_id TEXT UNIQUE,
    created_at TIMESTAMPTZ
);
"""

# Handles the case where the table already existed before `phone` was added —
# CREATE TABLE IF NOT EXISTS above won't touch an existing table's columns,
# so this runs every init_db() call and is a no-op once the column is there.
MIGRATIONS = [
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone TEXT;",
]


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is missing. Add a Postgres connection string to your "
            ".env (locally) or Vercel project env vars (hosted) — e.g. from "
            "Supabase: Project Settings -> Database -> Connection string."
        )
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            for migration in MIGRATIONS:
                cur.execute(migration)
        conn.commit()
    finally:
        conn.close()


def upsert_lead(lead: dict):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leads (
                    business_name, category, address, city, postcode, website,
                    phone, website_status, ai_tool_status, ai_tool_vendor,
                    lead_score, lead_status, source, place_id, created_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (place_id) DO UPDATE SET
                    business_name = EXCLUDED.business_name,
                    category = EXCLUDED.category,
                    address = EXCLUDED.address,
                    city = EXCLUDED.city,
                    postcode = EXCLUDED.postcode,
                    website = EXCLUDED.website,
                    phone = EXCLUDED.phone,
                    website_status = EXCLUDED.website_status,
                    ai_tool_status = EXCLUDED.ai_tool_status,
                    ai_tool_vendor = EXCLUDED.ai_tool_vendor,
                    lead_score = EXCLUDED.lead_score,
                    lead_status = EXCLUDED.lead_status,
                    source = EXCLUDED.source
                """,
                (
                    lead.get("business_name"), lead.get("category"), lead.get("address"),
                    lead.get("city"), lead.get("postcode"), lead.get("website"),
                    lead.get("phone"), lead.get("website_status"), lead.get("ai_tool_status"),
                    lead.get("ai_tool_vendor"), lead.get("lead_score"),
                    lead.get("lead_status"), lead.get("source"), lead.get("place_id"),
                    datetime.now(timezone.utc),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def fetch_leads(min_score: int = 0):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM leads WHERE lead_score >= %s ORDER BY lead_score DESC",
                (min_score,),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
