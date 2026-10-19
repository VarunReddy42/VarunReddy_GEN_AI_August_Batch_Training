"""
Central config for SmartHire GenAI.
Keeps model names, paths, and tunable params in one place so nothing
is hardcoded deep inside the parsing/search/generate modules.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths -------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
RESUMES_DIR = DATA_DIR / "resumes"
CAREER_NOTES_DIR = DATA_DIR / "career_notes"
VECTORSTORE_DIR = ROOT_DIR / "vectorstore"

# --- LLM settings --------------------------------------------------------
# Any provider covered in class works here — this project defaults to
# Gemini since that's what earlier course assignments used, but the
# resume_parser module is written provider-agnostic where it matters.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

# --- Chunking / search params -------------------------------------------
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_N_JOBS = 5

# --- Guardrail params ------------------------------------------------
MAX_RESUME_CHARS = 20_000
