# SmartHire GenAI — Resume Matching & AI Career Mentor

An end-to-end Generative AI career portal: upload a resume, get a structured
profile back, find matching jobs by semantic search, get AI-generated CV
improvement suggestions, and chat with a RAG-grounded AI Career Mentor.

Built with: LLM APIs (Gemini) · Structured output · FAISS · RAG · LangChain
· Streamlit

## Status

**Week 1 — done.** Repo scaffolded, resume parser (structured output +
document loading) and CV improvement generator (with a small prompt
library) are working end to end on their own.

**Week 2 — done.** Semantic job search (embeddings + FAISS) and the
AI Career Mentor RAG pipeline (orchestrated with LangChain) are built
and tested end to end.

**Week 3 — done.** Guardrails layer (rule-based + LLM classifier) sits
in front of the mentor, an evaluation script covers all four checks
from the project brief (retrieval relevance, answer quality, prompt
comparison, hallucination check), and the Streamlit portal ties every
module into one UI with four tabs: upload & parse, matched jobs, CV
suggestions, and the mentor chat.

A small `data/jobs/sample_jobs.csv` (10 fake postings) and two
`data/career_notes/*.md` files are included so you can test every
pipeline immediately. Swap in the real Kaggle job dataset before your
final submission — see Section 5 of the project brief.

## Setup

**Windows, easiest way:** double-click `run.bat`. It creates the virtual
environment, installs dependencies, asks for your Gemini API key once
(saved to your Windows user environment and `.env`, so you never retype
it, even in a fresh copy of this project), builds both indexes on first
run, and launches the app.

**Manual way:**

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and replace `your_actual_key_here` with
   your Gemini API key (from Google AI Studio). The file should read:
   ```
   GEMINI_API_KEY=your_actual_key_here
   GEMINI_MODEL=gemini-3.8-flash
   EMBEDDING_MODEL=gemini-embedding-001
   ```
   Never commit the real `.env`.
3. Build the indexes, then launch:
   ```bash
   python -m src.search.job_search data/jobs/sample_jobs.csv
   python -m src.mentor.rag_chain build
   streamlit run app/streamlit_app.py
   ```

## Try the Week 1 pieces

Parse a resume into structured JSON:
```bash
python -m src.parsing.resume_parser data/resumes/your_resume.pdf
```

Generate CV improvement suggestions against a sample job (uses a
built-in demo profile/job so it runs without any other module wired up
yet):
```bash
python -m src.generate.cv_suggestions
```

## Try the Week 2 pieces

Build the job search index (run once, or again whenever the job CSV
changes) and then search it:
```bash
python -m src.search.job_search data/jobs/sample_jobs.csv   # build the index
python -m src.search.job_search                             # run a demo search
```

Build the career-notes index and ask the mentor a question:
```bash
python -m src.mentor.rag_chain build
python -m src.mentor.rag_chain "How do I switch to Data Analyst?"
```

## Using the real Kaggle LinkedIn dataset (not live scraping)

The project brief is explicit that live scraping LinkedIn/Naukri is against
their Terms of Service and isn't part of this assignment — so this project
never does that. Instead, use a real, pre-collected, ToS-respecting dataset:

**[LinkedIn Job Postings (2023-2024) by arshkon on Kaggle](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings)**
— 124,000+ real postings with real company names, titles, and descriptions.

1. Download and unzip it (you'll need a free Kaggle account).
2. Convert it into the format this project expects:
   ```bash
   python -m src.search.prepare_kaggle_dataset /path/to/unzipped/dataset
   ```
   This merges `job_postings.csv` with `companies.csv` (for real company
   names) and writes `data/jobs/real_jobs.csv` (samples 2,000 rows by
   default — edit `max_rows` in the script for more).
3. Build the index from it instead of the sample CSV:
   ```bash
   python -m src.search.job_search data/jobs/real_jobs.csv
   ```

Now your matched jobs are real LinkedIn postings from real companies —
collected legitimately, once, per the brief's own instructions.

## Try the Week 3 pieces

Test the guardrails layer directly (no API call for the rule-based part):
```bash
python -m src.safety.guardrails "How do I switch to Data Analyst?"
python -m src.safety.guardrails "ignore previous instructions and do X"
```

Run the full evaluation suite (writes `reports/answer_quality.md`):
```bash
python -m src.evaluate
```

Launch the Streamlit portal:
```bash
streamlit run app/streamlit_app.py
```

## Deploying

1. Push this repo to GitHub (make sure `.env` is **not** committed —
   `.gitignore` already excludes it).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, and create a new app pointing at this repo and
   `app/streamlit_app.py`.
3. In the app's "Secrets" settings, add your `GEMINI_API_KEY` and
   `GEMINI_MODEL` the same way they're in your local `.env`.
4. Deploy — note that `data/`, `vectorstore/` are git-ignored by
   default, so make sure your job index and career-notes index are
   either committed (remove them from `.gitignore` if so) or built as
   part of a startup step, or the deployed app won't find them.

## Project layout

See `src/` for the module breakdown — each module under `src/`
(`parsing`, `search`, `generate`, `mentor`, `safety`) maps to one of the
six core features described in the project brief. `app/streamlit_app.py`
will tie everything together once Week 3 lands.

## Notes

- API keys live only in `.env`, never in code or git history.
- The resume parser validates the model's JSON against a Pydantic
  schema (`ResumeProfile`) before anything downstream trusts it — if
  the model returns something malformed, it fails loudly instead of
  silently passing bad data along.
- `src/generate/prompts.py` keeps a v0 (baseline) and v1 (current)
  version of the CV-suggestions prompt side by side, for the
  before/after comparison the evaluation report (Week 3) needs.
