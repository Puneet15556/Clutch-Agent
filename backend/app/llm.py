"""
LLM connection — every LangGraph node gets its model from here.

Provider is switchable via .env (LLM_PROVIDER = groq | gemini), so the same
agent logic runs on either. Default is Groq (free, no card).
"""
import os
from dotenv import load_dotenv

# override=True so .env always wins over a stale system env var.
load_dotenv(override=True)

PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()


def get_llm(temperature: float = 0.1):
    if PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY missing — add it to backend/.env")
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=key,
            temperature=temperature,
        )

    # default: Groq
    from langchain_groq import ChatGroq
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY missing — get a free key at console.groq.com/keys and add it to backend/.env"
        )
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        api_key=key,
        temperature=temperature,
    )
