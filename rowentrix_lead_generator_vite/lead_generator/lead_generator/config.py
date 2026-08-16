"""
Central place for all environment/config values.
Plain Python — no LangChain/LangGraph needed here, this is just app config.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    USE_LLM_SCORING = os.getenv("USE_LLM_SCORING", "false").lower() == "true"
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    @classmethod
    def validate(cls):
        if not cls.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is missing. Set it to your Supabase/Postgres "
                "connection string in .env (local) or Vercel env vars (hosted)."
            )
        if cls.USE_LLM_SCORING and not cls.OPENAI_API_KEY:
            raise RuntimeError(
                "USE_LLM_SCORING=true but OPENAI_API_KEY is missing."
            )
