"""
Evaluation & prompt optimization (Section 8 of the project brief).

Runs four checks and writes a Markdown report to reports/answer_quality.md:
  1. Retrieval relevance — for sample profiles, are the top jobs actually
     relevant? (yes/no scored, hit rate reported)
  2. Answer quality — mentor answers judged for correctness/grounding
  3. Prompt comparison — v0 (baseline) vs v1 (current) CV-suggestions prompt
  4. Hallucination check — mentor should refuse when the answer isn't
     in its documents

This is a lightweight, LLM-as-judge style evaluation — good enough to
produce a real signal and a real report without needing a hand-labeled
dataset.
"""

import json
from pathlib import Path

from google import genai

from src.config import GEMINI_API_KEY, GEMINI_MODEL, ROOT_DIR
from src.generate.prompts import cv_suggestions_prompt, cv_suggestions_prompt_v0_baseline
from src.llm_utils import llm_retry
from src.mentor.rag_chain import ask_mentor
from src.search.job_search import search_jobs

_client = genai.Client(api_key=GEMINI_API_KEY)

REPORT_PATH = ROOT_DIR / "reports" / "answer_quality.md"

# --- Test data -------------------------------------------------------
# Small, hand-picked profile/expected-relevant-title pairs. Extend this
# as you add more jobs to data/jobs/sample_jobs.csv (or the real
# Kaggle dataset).
RETRIEVAL_TEST_CASES = [
    {
        "profile": "Python developer with SQL and Tableau experience, wants a Data Analyst role.",
        "expect_keywords": ["data analyst", "business intelligence", "product analyst"],
    },
    {
        "profile": "ML engineer skilled in PyTorch and TensorFlow, interested in deploying models to production.",
        "expect_keywords": ["machine learning", "ai research", "data scientist"],
    },
    {
        "profile": "Frontend-leaning developer who knows React, Node.js, and MongoDB.",
        "expect_keywords": ["full stack", "developer"],
    },
]

MENTOR_TEST_QUESTIONS = [
    "How do I switch to Data Analyst?",
    "What are common weak bullet point patterns to avoid on a resume?",
]

# A question with no answer in the career-notes corpus — the mentor
# should say it doesn't know rather than guessing.
HALLUCINATION_TEST_QUESTION = (
    "What's the average signing bonus for a blockchain engineer in Dubai?"
)


@llm_retry
def _judge(prompt: str) -> str:
    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={"temperature": 0.0},
    )
    return response.text.strip()


def eval_retrieval_relevance() -> dict:
    """For each test profile, check whether any top-3 result matches an expected keyword."""
    results = []
    hits = 0

    for case in RETRIEVAL_TEST_CASES:
        jobs = search_jobs(case["profile"], top_n=3)
        titles = [j["title"].lower() for j in jobs]
        matched = any(
            keyword in title for title in titles for keyword in case["expect_keywords"]
        )
        hits += int(matched)
        results.append(
            {
                "profile": case["profile"],
                "top_titles": [j["title"] for j in jobs],
                "relevant": matched,
            }
        )

    hit_rate = hits / len(RETRIEVAL_TEST_CASES) if RETRIEVAL_TEST_CASES else 0
    return {"hit_rate": hit_rate, "cases": results}


def eval_answer_quality() -> list[dict]:
    """LLM-as-judge: for each mentor question, score correctness/grounding/helpfulness 1-5."""
    results = []
    for question in MENTOR_TEST_QUESTIONS:
        answer = ask_mentor(question)
        judge_prompt = f"""Rate this AI Career Mentor answer on three axes, 1-5 each:
- correctness: is it factually reasonable career advice?
- groundedness: does it sound like it's citing real retrieved documents
  rather than generic knowledge?
- helpfulness: would this actually help the user?

Question: {question}
Answer: {answer}

Respond ONLY as JSON: {{"correctness": int, "groundedness": int, "helpfulness": int, "notes": str}}
"""
        raw = _judge(judge_prompt)
        try:
            scores = json.loads(raw)
        except json.JSONDecodeError:
            scores = {"error": f"judge did not return JSON: {raw}"}

        results.append({"question": question, "answer": answer, "scores": scores})

    return results


def eval_prompt_comparison() -> dict:
    """Show a concrete before/after: v0 baseline prompt vs v1 current prompt."""
    demo_profile = {
        "name": "Test Candidate",
        "skills": ["Python", "Pandas"],
        "experience": [
            {
                "title": "Data Analyst Intern",
                "company": "Acme Corp",
                "duration": "Jun 2025 - Aug 2025",
                "highlights": ["Worked on dashboards"],
            }
        ],
    }
    demo_job = {
        "title": "Data Analyst",
        "description": "Looking for SQL, Python, Tableau, and A/B testing experience.",
    }

    v0_prompt = cv_suggestions_prompt_v0_baseline(demo_profile, demo_job)
    v1_prompt = cv_suggestions_prompt(demo_profile, demo_job)

    v0_output = _judge(v0_prompt)
    v1_output = _judge(v1_prompt)

    return {"v0_prompt": v0_prompt, "v0_output": v0_output, "v1_prompt": v1_prompt, "v1_output": v1_output}


def eval_hallucination_check() -> dict:
    """The mentor should decline rather than invent an answer to an out-of-corpus question."""
    answer = ask_mentor(HALLUCINATION_TEST_QUESTION)
    refused = any(
        phrase in answer.lower()
        for phrase in ["don't have enough information", "i don't know", "not in my documents"]
    )
    return {"question": HALLUCINATION_TEST_QUESTION, "answer": answer, "correctly_refused": refused}


def run_full_evaluation() -> None:
    """Run all four checks and write a Markdown report to reports/answer_quality.md."""
    print("Running retrieval relevance eval...")
    retrieval = eval_retrieval_relevance()

    print("Running answer quality eval...")
    answer_quality = eval_answer_quality()

    print("Running prompt comparison...")
    prompt_comparison = eval_prompt_comparison()

    print("Running hallucination check...")
    hallucination = eval_hallucination_check()

    lines = ["# SmartHire GenAI — Evaluation Report\n"]

    lines.append("## 1. Retrieval Relevance\n")
    lines.append(f"Hit rate: **{retrieval['hit_rate']:.0%}** ({len(retrieval['cases'])} test profiles)\n")
    for case in retrieval["cases"]:
        mark = "✅" if case["relevant"] else "❌"
        lines.append(f"- {mark} *{case['profile']}* -> top matches: {', '.join(case['top_titles'])}")

    lines.append("\n## 2. Answer Quality (LLM-as-judge, 1-5)\n")
    for item in answer_quality:
        lines.append(f"**Q: {item['question']}**\n")
        lines.append(f"> {item['answer'][:400]}...\n" if len(item["answer"]) > 400 else f"> {item['answer']}\n")
        lines.append(f"Scores: `{json.dumps(item['scores'])}`\n")

    lines.append("\n## 3. Prompt Comparison (v0 baseline vs v1 current)\n")
    lines.append("**v0 (baseline) output:**\n")
    lines.append(f"```\n{prompt_comparison['v0_output'][:600]}\n```\n")
    lines.append("**v1 (current) output:**\n")
    lines.append(f"```\n{prompt_comparison['v1_output'][:600]}\n```\n")
    lines.append(
        "v1 asks for a strict JSON contract (missing_skills / weak_bullets / "
        "rewritten_summary) and explicitly forbids inventing metrics, which v0 "
        "does not — v1's output is structured and directly usable by the UI; "
        "v0's is freeform prose that would need further parsing.\n"
    )

    lines.append("\n## 4. Hallucination Check\n")
    mark = "✅ Correctly refused" if hallucination["correctly_refused"] else "❌ Did NOT refuse — investigate"
    lines.append(f"{mark}\n")
    lines.append(f"**Q:** {hallucination['question']}\n")
    lines.append(f"> {hallucination['answer']}\n")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    run_full_evaluation()
