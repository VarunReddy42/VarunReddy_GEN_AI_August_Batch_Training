"""SmartHire GenAI — premium Streamlit portal.

Preserves the project's existing AI pipelines while providing a polished,
responsive application shell with persistent navigation, animated section
transitions, rich cards, and clear workflow state.

Run with:
    streamlit run app/streamlit_app.py
"""

import sys
import tempfile
from html import escape
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generate.cv_suggestions import generate_cv_suggestions
from src.mentor.rag_chain import NOTES_INDEX_DIR, ask_mentor
from src.parsing.loader import load_resume
from src.parsing.resume_parser import parse_resume
from src.search.job_search import INDEX_PATH as JOB_INDEX_PATH
from src.search.job_search import search_jobs

st.set_page_config(
    page_title="SmartHire — AI Career Copilot",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Premium visual system
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #08090f;
    --bg-soft: #0d0f18;
    --panel: #11131d;
    --panel-2: #151824;
    --panel-hover: #191d2a;
    --ink: #f6f7fb;
    --muted: #969caf;
    --muted-2: #697084;
    --line: rgba(255,255,255,.08);
    --line-strong: rgba(255,255,255,.14);
    --violet: #8b5cf6;
    --violet-2: #a78bfa;
    --cyan: #22d3ee;
    --mint: #34d399;
    --amber: #fbbf24;
    --danger: #fb7185;
    --shadow: 0 20px 60px rgba(0,0,0,.26);
}

* { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
html { font-size: 115% !important; }
.stApp { background: var(--bg); color: var(--ink); }
[data-testid="stHeader"] { background: rgba(8,9,15,.82); }
[data-testid="stToolbar"] { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem; max-width: 1500px; }

h1,h2,h3,h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -.025em; }

/* Animated page canvas: Streamlit reruns are given a subtle glide rather than
   an abrupt visual swap. */
.page-enter { animation: pageIn .42s cubic-bezier(.2,.8,.2,1) both; }
@keyframes pageIn {
  from { opacity: 0; transform: translate3d(0,12px,0); filter: blur(2px); }
  to { opacity: 1; transform: translate3d(0,0,0); filter: blur(0); }
}

/* Navigation rail */
section[data-testid="stSidebar"] {
    background: #0a0b12;
    border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] > div { padding: 1.3rem 1rem; }
.brand { display:flex; align-items:center; gap:.8rem; padding:.5rem .35rem 1.4rem; }
.brand-mark {
    width:42px; height:42px; border-radius:13px; display:grid; place-items:center;
    background: #171326; border:1px solid rgba(167,139,250,.35);
    color:#c4b5fd; font-size:20px; box-shadow: 0 0 28px rgba(139,92,246,.16);
}
.brand-name { font-family:'Space Grotesk'; font-weight:700; font-size:1.03rem; }
.brand-sub { color:var(--muted-2); font-size:.7rem; margin-top:2px; }
.nav-label { color:#60687a; font-size:.68rem; text-transform:uppercase; letter-spacing:.14em; font-weight:700; margin:.4rem .4rem .6rem; }

/* Native radio is transformed into a clean navigation menu. */
div[data-testid="stSidebar"] div[role="radiogroup"] { gap: .35rem; }
div[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: transparent; border:1px solid transparent; border-radius:12px;
    padding:.68rem .75rem; transition:all .2s ease; cursor:pointer;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background:rgba(255,255,255,.04); border-color:var(--line);
    transform:translateX(2px);
}
div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
    background:linear-gradient(90deg, rgba(139,92,246,.17), rgba(139,92,246,.04));
    border-color:rgba(139,92,246,.22);
}
div[data-testid="stSidebar"] div[role="radiogroup"] label p { font-size:.9rem; font-weight:600; }
div[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display:none; }

.rail-status { margin-top:1.3rem; padding:.9rem; border:1px solid var(--line); background:rgba(255,255,255,.025); border-radius:14px; }
.rail-status-title { color:#7d8598; font-size:.68rem; text-transform:uppercase; letter-spacing:.12em; font-weight:700; margin-bottom:.7rem; }
.status-row { display:flex; align-items:center; gap:.55rem; margin:.42rem 0; font-size:.78rem; color:#aeb4c3; }
.dot { width:7px; height:7px; border-radius:50%; background:#3d4352; box-shadow:0 0 0 3px rgba(61,67,82,.12); }
.dot.ok { background:var(--mint); box-shadow:0 0 0 3px rgba(52,211,153,.10); }

/* Hero */
.hero {
    position:relative; overflow:hidden; padding:2.15rem 2.25rem; border-radius:24px;
    border:1px solid rgba(167,139,250,.17);
    background: radial-gradient(circle at 88% 12%, rgba(139,92,246,.20), transparent 31%),
                radial-gradient(circle at 55% 120%, rgba(34,211,238,.10), transparent 32%),
                linear-gradient(135deg,#121322,#0e1019 58%,#11101d);
    box-shadow:var(--shadow); margin-bottom:1.35rem;
}
.hero::after { content:""; position:absolute; inset:0; pointer-events:none; background:linear-gradient(110deg,transparent 0%,rgba(255,255,255,.025) 50%,transparent 100%); transform:translateX(-100%); animation: sheen 6s ease-in-out infinite; }
@keyframes sheen { 0%,60%{transform:translateX(-100%)} 85%,100%{transform:translateX(100%)} }
.eyebrow { color:#b7a2ff; font-size:.72rem; text-transform:uppercase; letter-spacing:.16em; font-weight:700; }
.hero h1 { font-size:clamp(2rem,4vw,3.3rem); line-height:1.02; margin:.45rem 0 .65rem; }
.hero p { color:#a8adbd; max-width:760px; margin:0; font-size:1rem; line-height:1.65; }
.hero-grid { display:grid; grid-template-columns:1fr auto; gap:1rem; align-items:end; }
.hero-orb { width:110px; height:110px; border-radius:32px; display:grid; place-items:center; background:#171326; border:1px solid rgba(167,139,250,.24); color:#c4b5fd; font-size:43px; box-shadow:inset 0 0 40px rgba(139,92,246,.10),0 20px 50px rgba(0,0,0,.22); }

/* Cards and stats */
.card { background:linear-gradient(180deg,rgba(255,255,255,.045),rgba(255,255,255,.022)); border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.25rem; box-shadow:0 10px 35px rgba(0,0,0,.12); }
.card-hover { transition:transform .22s ease,border-color .22s ease,background .22s ease; }
.card-hover:hover { transform:translateY(-3px); border-color:rgba(167,139,250,.22); background:var(--panel-hover); }
.stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin:1rem 0 1.2rem; }
.stat { padding:1rem; border:1px solid var(--line); border-radius:16px; background:rgba(255,255,255,.025); }
.stat-k { color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.1em; }
.stat-v { font-family:'Space Grotesk'; font-size:1.65rem; font-weight:700; margin-top:.25rem; }
.stat-h { color:var(--muted-2); font-size:.72rem; margin-top:.2rem; }
.section-title { font-size:1.28rem; margin:0 0 .25rem; }
.section-sub { color:var(--muted); font-size:.85rem; margin:0 0 1rem; }

/* Chips */
.chips { display:flex; flex-wrap:wrap; gap:.45rem; }
.chip { display:inline-flex; align-items:center; min-height:28px; padding:.25rem .62rem; border-radius:999px; color:#d8d0ff; background:#18142a; border:1px solid rgba(139,92,246,.20); font-size:.76rem; font-weight:600; }

/* Job cards */
.job { padding:1.15rem; border-radius:18px; border:1px solid var(--line); background:linear-gradient(180deg,#12151f,#0f1119); margin-bottom:.75rem; transition:all .22s ease; }
.job:hover { transform:translateY(-2px); border-color:rgba(34,211,238,.20); box-shadow:0 14px 40px rgba(0,0,0,.18); }
.job-top { display:flex; gap:1rem; justify-content:space-between; align-items:flex-start; }
.job-title { font-family:'Space Grotesk'; font-size:1.04rem; font-weight:700; }
.job-company { color:#8f96a8; font-size:.8rem; margin-top:.18rem; }
.job-desc { color:#adb2c0; font-size:.82rem; line-height:1.58; margin-top:.8rem; }
.score { flex:0 0 auto; padding:.35rem .6rem; border-radius:10px; color:#0b1513; background:#6ee7b7; font-weight:800; font-size:.72rem; }

/* Icon-safe badges: opaque surfaces guarantee the glyph stays readable over any background. */
.icon-badge { width:38px; height:38px; border-radius:12px; display:grid; place-items:center; flex:0 0 auto; background:#19152a; border:1px solid rgba(167,139,250,.25); color:#c4b5fd; font-size:17px; }
.feature-row { display:flex; gap:.8rem; align-items:flex-start; }
.feature-row + .feature-row { margin-top:.9rem; }
.feature-title { font-weight:700; font-size:.86rem; }
.feature-copy { color:var(--muted); font-size:.76rem; line-height:1.45; margin-top:.15rem; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div, .stFileUploader section {
    background:#0e1018 !important; color:#f4f5f8 !important; border-color:var(--line-strong) !important; border-radius:12px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus { border-color:rgba(139,92,246,.65) !important; box-shadow:0 0 0 3px rgba(139,92,246,.09) !important; }
label { color:#aeb4c3 !important; font-size:.78rem !important; font-weight:600 !important; }

/* Buttons */
.stButton > button { width:100%; border-radius:12px; border:1px solid rgba(167,139,250,.25); background:#171326; color:#f5f3ff; font-weight:700; min-height:43px; transition:all .2s ease; }
.stButton > button:hover { transform:translateY(-1px); border-color:rgba(167,139,250,.5); background:#20193a; color:#fff; box-shadow:0 8px 25px rgba(139,92,246,.13); }
.primary-btn .stButton > button { background:linear-gradient(135deg,#7c3aed,#8b5cf6); border-color:transparent; }

/* Chat */
[data-testid="stChatMessage"] { background:rgba(255,255,255,.025); border:1px solid var(--line); border-radius:16px; margin:.55rem 0; }
[data-testid="stChatInput"] { border-color:var(--line-strong) !important; }

/* Progress / separators */
.workflow { display:flex; gap:.45rem; margin:.9rem 0 1.4rem; }
.workflow-item { flex:1; display:flex; align-items:center; gap:.45rem; color:#6e7586; font-size:.7rem; font-weight:700; }
.workflow-item::after { content:""; height:1px; flex:1; background:var(--line); margin-left:.3rem; }
.workflow-item:last-child::after { display:none; }
.workflow-item.active { color:#c4b5fd; }
.workflow-num { width:24px; height:24px; border-radius:8px; display:grid; place-items:center; background:#13151e; border:1px solid var(--line); }
.workflow-item.active .workflow-num { background:#211844; border-color:rgba(139,92,246,.35); color:#c4b5fd; }

@media (max-width: 900px) {
  .block-container { padding:1.2rem 1rem 3rem; }
  .hero-grid { grid-template-columns:1fr; }
  .hero-orb { display:none; }
  .stat-grid { grid-template-columns:1fr; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def init_state():
    defaults = {
        "profile": None,
        "resume_name": None,
        "matched_jobs": [],
        "selected_job": None,
        "suggestions": None,
        "chat_history": [],
        "nav": "Overview",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def esc(value) -> str:
    return escape(str(value or ""))


def chips(items) -> str:
    if not items:
        return '<span style="color:#697084;font-size:.78rem">None detected</span>'
    return '<div class="chips">' + "".join(f'<span class="chip">{esc(x)}</span>' for x in items) + "</div>"


def status_dot(ready: bool) -> str:
    return '<span class="dot ok"></span>' if ready else '<span class="dot"></span>'


def hero(title: str, subtitle: str, icon: str, eyebrow: str):
    st.markdown(
        f'''<div class="hero page-enter"><div class="hero-grid"><div>
        <div class="eyebrow">{esc(eyebrow)}</div>
        <h1>{esc(title)}</h1><p>{esc(subtitle)}</p>
        </div><div class="hero-orb">{esc(icon)}</div></div></div>''',
        unsafe_allow_html=True,
    )


def workflow(active: int):
    labels = ["Profile", "Jobs", "Tailor", "Mentor"]
    html = '<div class="workflow">'
    for i, label in enumerate(labels, 1):
        cls = "active" if i <= active else ""
        html += f'<div class="workflow-item {cls}"><span class="workflow-num">{i}</span>{label}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def pipeline_card():
    profile_ready = st.session_state.profile is not None
    jobs_ready = JOB_INDEX_PATH.exists()
    notes_ready = NOTES_INDEX_DIR.exists()
    st.markdown(
        f'''<div class="rail-status"><div class="rail-status-title">System readiness</div>
        <div class="status-row">{status_dot(profile_ready)} Resume profile</div>
        <div class="status-row">{status_dot(jobs_ready)} Job search index</div>
        <div class="status-row">{status_dot(notes_ready)} Mentor knowledge base</div>
        </div>''',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '''<div class="brand"><div class="brand-mark">✦</div><div><div class="brand-name">SmartHire</div><div class="brand-sub">AI CAREER COPILOT</div></div></div>''',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
    pages = [
        "⌂  Overview",
        "◈  Resume Studio",
        "⌕  Job Matches",
        "✦  CV Tailor",
        "◉  Career Mentor",
    ]
    current_label = st.session_state.nav
    current_idx = [p.split("  ", 1)[1] for p in pages].index(current_label)
    chosen = st.radio(
        "Navigation",
        pages,
        index=current_idx,
        label_visibility="collapsed",
        key="nav_radio",
    )
    st.session_state.nav = chosen.split("  ", 1)[1]
    pipeline_card()

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
page = st.session_state.nav

if page == "Overview":
    hero(
        "Your career, with an AI copilot.",
        "Turn one resume into a structured profile, semantic job matches, targeted CV improvements, and grounded career guidance.",
        "✦",
        "SMARTCAREER WORKSPACE",
    )
    workflow(1 if not st.session_state.profile else 4)

    if not st.session_state.profile:
        left, right = st.columns([1.35, .85], gap="large")
        with left:
            st.markdown('<div class="card page-enter">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Start with your resume</div>', unsafe_allow_html=True)
            st.markdown('<p class="section-sub">Upload a PDF or DOCX and let SmartHire build your career profile.</p>', unsafe_allow_html=True)
            st.markdown('<div class="feature-row"><div class="icon-badge">↗</div><div><div class="feature-title">Structured profile</div><div class="feature-copy">Extract skills, experience, education and likely target role.</div></div></div>', unsafe_allow_html=True)
            st.markdown('<div class="feature-row"><div class="icon-badge">⌕</div><div><div class="feature-title">Semantic job discovery</div><div class="feature-copy">Match your profile against the indexed job corpus using embeddings.</div></div></div>', unsafe_allow_html=True)
            st.markdown('<div class="feature-row"><div class="icon-badge">✦</div><div><div class="feature-title">Grounded mentor</div><div class="feature-copy">Ask career questions against the supplied career-note knowledge base.</div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="card page-enter">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Pipeline</div>', unsafe_allow_html=True)
            st.markdown('<p class="section-sub">Everything stays connected through session state.</p>', unsafe_allow_html=True)
            for number, label, ready in [
                ("01", "Resume parsed", False),
                ("02", "Jobs matched", False),
                ("03", "CV tailored", False),
                ("04", "Mentor ready", NOTES_INDEX_DIR.exists()),
            ]:
                st.markdown(f'<div class="status-row"><span style="font-family:Space Grotesk;color:#777f91;width:25px">{number}</span>{status_dot(ready)} {label}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        profile = st.session_state.profile
        st.markdown('<div class="stat-grid page-enter">', unsafe_allow_html=True)
        for label, value, hint in [
            ("Skills", len(profile.skills), "detected"),
            ("Experience", len(profile.experience), "roles listed"),
            ("Education", len(profile.education), "credentials"),
        ]:
            st.markdown(f'<div class="stat"><div class="stat-k">{label}</div><div class="stat-v">{value}</div><div class="stat-h">{hint}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        a, b = st.columns([1.2, .8], gap="large")
        with a:
            st.markdown('<div class="card card-hover page-enter"><div class="section-title">Profile snapshot</div><p class="section-sub">Your parsed career identity.</p>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-family:Space Grotesk;font-size:1.25rem;font-weight:700">{esc(profile.name)}</div><div style="color:#8f96a8;font-size:.8rem;margin:.2rem 0 .8rem">{esc(profile.target_role or "Target role not inferred")}</div>', unsafe_allow_html=True)
            st.markdown(chips(profile.skills[:10]), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with b:
            st.markdown('<div class="card card-hover page-enter"><div class="section-title">Next move</div><p class="section-sub">Continue the workflow.</p>', unsafe_allow_html=True)
            st.markdown('<div class="feature-row"><div class="icon-badge">⌕</div><div><div class="feature-title">Explore matched jobs</div><div class="feature-copy">Find roles aligned with your profile.</div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif page == "Resume Studio":
    hero("Resume Studio", "Upload once. SmartHire turns your document into the structured profile used everywhere else.", "↗", "01 / PROFILE")
    workflow(1 if not st.session_state.profile else 2)
    uploaded_file = st.file_uploader("Resume document", type=["pdf", "docx"], label_visibility="visible")
    if uploaded_file:
        st.markdown(f'<div class="card" style="margin:.7rem 0"><div style="display:flex;align-items:center;gap:.7rem"><div class="icon-badge">PDF</div><div><b>{esc(uploaded_file.name)}</b><div style="color:#777f91;font-size:.72rem">{round(uploaded_file.size/1024,1)} KB · ready to parse</div></div></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        parse_clicked = st.button("Parse resume →")
        st.markdown('</div>', unsafe_allow_html=True)
        if parse_clicked:
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            with st.spinner("Building your career profile…"):
                try:
                    text = load_resume(tmp_path)
                    profile = parse_resume(text)
                    st.session_state.profile = profile
                    st.session_state.resume_name = uploaded_file.name
                    st.session_state.matched_jobs = []
                    st.session_state.suggestions = None
                    st.session_state.nav = "Resume Studio"
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not parse this resume: {exc}")
    if st.session_state.profile:
        profile = st.session_state.profile
        st.markdown('<div class="card page-enter" style="margin-top:1.1rem"><div class="section-title">Parsed profile</div><p class="section-sub">Validated structured output from the resume parser.</p>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-family:Space Grotesk;font-size:1.45rem;font-weight:700">{esc(profile.name)}</div><div style="color:#8f96a8;font-size:.8rem;margin:.2rem 0 1rem">{esc(profile.email)} · {esc(profile.phone)} · {esc(profile.target_role or "Target role not inferred")}</div>', unsafe_allow_html=True)
        if profile.summary:
            st.info(profile.summary)
        st.markdown('<div style="font-weight:700;font-size:.82rem;margin:1rem 0 .5rem">Skills</div>', unsafe_allow_html=True)
        st.markdown(chips(profile.skills), unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown('<div style="font-weight:700;font-size:.82rem;margin:1rem 0 .5rem">Experience</div>', unsafe_allow_html=True)
            for exp in profile.experience:
                st.markdown(f'<div style="padding:.65rem 0;border-bottom:1px solid var(--line)"><b>{esc(exp.title)}</b><div style="color:#858c9e;font-size:.75rem">{esc(exp.company)} · {esc(exp.duration)}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div style="font-weight:700;font-size:.82rem;margin:1rem 0 .5rem">Education</div>', unsafe_allow_html=True)
            for edu in profile.education:
                st.markdown(f'<div style="padding:.65rem 0;border-bottom:1px solid var(--line)"><b>{esc(edu.degree)}</b><div style="color:#858c9e;font-size:.75rem">{esc(edu.institution)} · {esc(edu.year)}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Job Matches":
    hero("Job Matches", "Search the indexed job corpus with the semantic signal from your profile—not just keyword overlap.", "⌕", "02 / DISCOVERY")
    workflow(2 if st.session_state.profile else 1)
    if not st.session_state.profile:
        st.warning("Parse a resume first to generate profile-aware matches.")
    elif not JOB_INDEX_PATH.exists():
        st.error("The job index is not built yet. Run `python -m src.search.job_search data/jobs/sample_jobs.csv` before searching.")
    else:
        profile = st.session_state.profile
        c1, c2 = st.columns([1, .3])
        with c1:
            st.markdown(f'<div class="card"><div class="section-title">Searching for</div><div style="font-family:Space Grotesk;font-weight:700;font-size:1.05rem">{esc(profile.target_role or "Your next role")}</div><div style="margin-top:.5rem">{chips(profile.skills[:8])}</div></div>', unsafe_allow_html=True)
        with c2:
            top_n = st.select_slider("Results", options=[3,5,7,10], value=5)
            find_clicked = st.button("Find matches")
        if find_clicked:
            query_text = f"{profile.target_role} with skills: {', '.join(profile.skills)}"
            with st.spinner("Ranking relevant roles…"):
                try:
                    st.session_state.matched_jobs = search_jobs(query_text, top_n=top_n)
                except Exception as exc:
                    st.error(f"Job search failed: {exc}")
        jobs = st.session_state.matched_jobs
        if jobs:
            st.markdown(f'<div style="color:#858c9e;font-size:.76rem;margin:1.1rem 0 .6rem">{len(jobs)} semantic matches · ranked by profile similarity</div>', unsafe_allow_html=True)
            for i, job in enumerate(jobs):
                score_pct = max(0, min(100, round(float(job.get("similarity_score", 0)) * 100)))
                col = st.container()
                with col:
                    st.markdown(f'''<div class="job page-enter"><div class="job-top"><div><div class="job-title">{esc(job.get("title"))}</div><div class="job-company">{esc(job.get("company"))}</div></div><span class="score">{score_pct}% match</span></div><div class="job-desc">{esc(job.get("description"))}</div></div>''', unsafe_allow_html=True)
                if st.button("Use this role for CV tailoring", key=f"tailor_{i}"):
                    st.session_state.selected_job = job
                    st.session_state.nav = "CV Tailor"
                    st.rerun()
        else:
            st.markdown('<div class="card" style="margin-top:1rem;text-align:center;padding:2rem"><div class="icon-badge" style="margin:0 auto .8rem">⌕</div><b>No matches loaded yet</b><div style="color:#777f91;font-size:.78rem;margin-top:.25rem">Click “Find matches” to rank the indexed roles.</div></div>', unsafe_allow_html=True)

elif page == "CV Tailor":
    hero("CV Tailor", "Compare your profile with a target role and get structured, evidence-safe improvements you can act on.", "✦", "03 / TAILOR")
    workflow(3 if st.session_state.profile else 1)
    if not st.session_state.profile:
        st.warning("Parse a resume first.")
    else:
        profile = st.session_state.profile
        default_title = (st.session_state.selected_job or {}).get("title") or profile.target_role
        default_desc = (st.session_state.selected_job or {}).get("description", "")
        left, right = st.columns([.85, 1.15], gap="large")
        with left:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            job_title = st.text_input("Target role", value=default_title or "")
            job_description = st.text_area("Job description", value=default_desc, height=270, placeholder="Paste the target job description here…")
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            generate_clicked = st.button("Generate tailored improvements →")
            st.markdown('</div></div>', unsafe_allow_html=True)
        with right:
            suggestions = st.session_state.suggestions
            if generate_clicked and job_description:
                with st.spinner("Finding gaps and rewriting weak signals…"):
                    try:
                        suggestions = generate_cv_suggestions(profile.model_dump(), {"title": job_title, "description": job_description})
                        st.session_state.suggestions = suggestions
                    except Exception as exc:
                        st.error(f"Could not generate suggestions: {exc}")
            if suggestions:
                missing = suggestions.missing_skills or []
                st.markdown('<div class="card page-enter"><div class="section-title">Skill gaps</div><p class="section-sub">Skills present in the target description but not represented in the parsed profile.</p>', unsafe_allow_html=True)
                st.markdown(chips(missing), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                for i, wb in enumerate(suggestions.weak_bullets or []):
                    st.markdown(f'<div class="card page-enter" style="margin-top:.7rem"><div style="display:flex;gap:.7rem;align-items:center"><div class="icon-badge">↻</div><div class="section-title">Bullet rewrite {i+1}</div></div><div style="margin-top:.8rem;color:#7f8798;font-size:.68rem;text-transform:uppercase;letter-spacing:.1em">Original</div><div style="font-size:.82rem;line-height:1.55;margin-top:.2rem">{esc(wb.original)}</div><div style="margin-top:.75rem;color:#7f8798;font-size:.68rem;text-transform:uppercase;letter-spacing:.1em">Why it is weak</div><div style="font-size:.78rem;color:#9aa1b1;margin-top:.2rem">{esc(wb.why_weak)}</div><div style="margin-top:.75rem;color:#9d8aff;font-size:.68rem;text-transform:uppercase;letter-spacing:.1em">Improved</div><div style="font-size:.84rem;line-height:1.55;margin-top:.2rem">{esc(wb.improved)}</div></div>', unsafe_allow_html=True)
                if suggestions.rewritten_summary:
                    st.markdown(f'<div class="card page-enter" style="margin-top:.7rem"><div class="section-title">Rewritten summary</div><p class="section-sub">A concise version aligned to the target role without inventing metrics.</p><div style="padding:.9rem;border-radius:12px;background:#0c0f17;border:1px solid var(--line);color:#d5d8e1;font-size:.84rem;line-height:1.65">{esc(suggestions.rewritten_summary)}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card" style="height:100%;display:grid;place-items:center;min-height:390px;text-align:center"><div><div class="icon-badge" style="margin:0 auto .9rem">✦</div><b>Your tailored analysis will appear here</b><div style="color:#777f91;font-size:.78rem;max-width:360px;margin:.35rem auto">Select a matched role or paste a job description, then generate improvements.</div></div></div>', unsafe_allow_html=True)

elif page == "Career Mentor":
    hero("Career Mentor", "A RAG-grounded career conversation. Ask questions, get answers tied to the project's career-note corpus.", "◉", "04 / MENTOR")
    workflow(4 if st.session_state.profile else 1)
    if not NOTES_INDEX_DIR.exists():
        st.error("The mentor knowledge base is not built yet. Run `python -m src.mentor.rag_chain build` first.")
    else:
        if not st.session_state.chat_history:
            st.markdown('<div class="card" style="margin-bottom:1rem"><div class="section-title">Try asking</div><div class="chips"><span class="chip">How do I switch to Data Analyst?</span><span class="chip">What makes a resume bullet stronger?</span><span class="chip">How should I plan my transition?</span></div></div>', unsafe_allow_html=True)
        for role, message in st.session_state.chat_history:
            with st.chat_message(role):
                st.write(message)
        question = st.chat_input("Ask your career question…")
        if question:
            st.session_state.chat_history.append(("user", question))
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                with st.spinner("Retrieving career guidance…"):
                    try:
                        answer = ask_mentor(question)
                    except Exception as exc:
                        answer = f"Something went wrong: {exc}"
                st.write(answer)
            st.session_state.chat_history.append(("assistant", answer))
