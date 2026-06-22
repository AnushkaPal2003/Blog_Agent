from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from graph import app
from utils.helpers import (
    safe_slug,
    bundle_zip,
    list_past_blogs,
    read_md_file,
    extract_title_from_md,
    try_stream,
    extract_latest_state,
)

# Page config 

st.set_page_config(
    page_title="Blog Writing Agent",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS 

st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f0f13;
    border-right: 1px solid #1e1e2e;
}
[data-testid="stSidebar"] * { color: #e2e2f0 !important; }
[data-testid="stSidebar"] .stTextArea textarea {
    background: #1a1a28 !important;
    border: 1px solid #2e2e48 !important;
    border-radius: 8px !important;
    color: #e2e2f0 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #6c63ff, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
[data-testid="stSidebar"] .stButton > button:hover { opacity: 0.85 !important; }

/* ── Hero header ── */
.hero {
    background: linear-gradient(135deg, #0f0f13 0%, #1a1a28 50%, #0f0f13 100%);
    border: 1px solid #6c63ff40;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
}
.hero h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.02em;
}
.hero p {
    color: #a0a0c0;
    margin: 0;
    font-size: 0.95rem;
}
.badge-row { display: flex; gap: 0.5rem; margin-top: 0.8rem; flex-wrap: wrap; }
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.25rem 0.65rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    border: 1px solid;
}
.badge-purple { background: #6c63ff15; border-color: #6c63ff40; color: #6c63ff; }
.badge-teal   { background: #06b6d415; border-color: #06b6d440; color: #0891b2; }
.badge-green  { background: #10b98115; border-color: #10b98140; color: #059669; }
.badge-amber  { background: #f59e0b15; border-color: #f59e0b40; color: #d97706; }

/* ── Stat cards ── */
.stat-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.stat-card {
    flex: 1;
    min-width: 130px;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.stat-card .stat-val {
    font-size: 1.6rem;
    font-weight: 700;
    color: #6c63ff;
    line-height: 1;
}
.stat-card .stat-lbl {
    font-size: 0.72rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
}

/* ── Node progress pill ── */
.node-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #f0f0ff;
    border: 1px solid #c7d2fe;
    border-radius: 20px;
    padding: 0.3rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: #4338ca;
    margin: 0.2rem 0;
}

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent;
    border-bottom: 2px solid #e5e7eb;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* ── Blog preview ── */
.blog-preview {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.7;
}
.blog-preview h1 { font-size: 1.8rem; font-weight: 700; color: #111827; }
.blog-preview h2 { font-size: 1.2rem; font-weight: 600; color: #1f2937; border-bottom: 1px solid #f3f4f6; padding-bottom: 0.3rem; }
.blog-preview a { color: #6c63ff; text-decoration: underline; }
.blog-preview code {
    background: #f8f8ff;
    border: 1px solid #e0e0ff;
    border-radius: 4px;
    padding: 0.1rem 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85em;
}
.blog-preview pre {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 1.2rem;
    overflow-x: auto;
}
.blog-preview pre code {
    background: transparent;
    border: none;
    color: #e2e2f0;
    font-size: 0.82rem;
}
.blog-preview img {
    max-width: 100%;
    border-radius: 8px;
    margin: 1rem 0;
    border: 1px solid #e5e7eb;
}
.blog-preview blockquote {
    border-left: 3px solid #6c63ff;
    padding-left: 1rem;
    color: #6b7280;
    margin: 1rem 0;
}

/* ── Evidence card ── */
.evidence-card {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
}
.evidence-card a { color: #6c63ff; font-weight: 500; text-decoration: none; }
.evidence-card a:hover { text-decoration: underline; }
.evidence-card .ev-meta { font-size: 0.75rem; color: #9ca3af; margin-top: 0.2rem; }

/* ── Force sidebar toggle visible ── */
[data-testid="collapsedControl"] {
    background: #6c63ff !important;
    border-radius: 0 8px 8px 0 !important;
    color: white !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}
section[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
}

/* ── Log area ── */
.log-box {
    background: #0f0f13;
    border-radius: 10px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #a0a0c0;
    max-height: 400px;
    overflow-y: auto;
}

/* ── Download buttons ── */
.dl-row { display: flex; gap: 0.8rem; flex-wrap: wrap; margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)


# Markdown renderer (handles local images + clickable links) 

_MD_IMG_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")
_CAPTION_RE = re.compile(r"^\*(?P<cap>.+)\*$")


def render_blog_markdown(md: str):
    """Render markdown with local image support and clickable source links."""
    matches = list(_MD_IMG_RE.finditer(md))
    if not matches:
        st.markdown(f'<div class="blog-preview">', unsafe_allow_html=True)
        st.markdown(md, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    parts: List[Tuple[str, str]] = []
    last = 0
    for m in matches:
        before = md[last:m.start()]
        if before:
            parts.append(("md", before))
        parts.append(("img", f"{m.group('alt')}|||{m.group('src')}"))
        last = m.end()
    if md[last:]:
        parts.append(("md", md[last:]))

    st.markdown('<div class="blog-preview">', unsafe_allow_html=True)
    i = 0
    while i < len(parts):
        kind, payload = parts[i]
        if kind == "md":
            st.markdown(payload, unsafe_allow_html=True)
            i += 1
            continue

        alt, src = payload.split("|||", 1)
        caption = None
        if i + 1 < len(parts) and parts[i + 1][0] == "md":
            nxt = parts[i + 1][1].lstrip()
            first = nxt.splitlines()[0].strip() if nxt.strip() else ""
            m_cap = _CAPTION_RE.match(first)
            if m_cap:
                caption = m_cap.group("cap").strip()
                rest = "\n".join(nxt.splitlines()[1:])
                parts[i + 1] = ("md", rest)

        if src.startswith("http://") or src.startswith("https://"):
            st.image(src, caption=caption or alt or None, use_container_width=True)
        else:
            img_path = Path(src.strip().lstrip("./")).resolve()
            if img_path.exists():
                st.image(str(img_path), caption=caption or alt or None, use_container_width=True)
            else:
                st.warning(f"Image not found: `{src}`")
        i += 1

    st.markdown('</div>', unsafe_allow_html=True)


# Session state init 

if "last_out" not in st.session_state:
    st.session_state["last_out"] = None
if "run_logs" not in st.session_state:
    st.session_state["run_logs"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())


# Sidebar 

with st.sidebar:
    st.markdown("### ✍️ Blog Writing Agent")
    st.markdown("---")

    st.markdown("**🔑 OpenAI API Key**")
    openai_key = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-proj-...",
        label_visibility="collapsed",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    else:
        st.caption("⚠️ Enter your OpenAI API key to generate images.")

    st.markdown("---")
    st.markdown("**📝 New Blog**")
    topic = st.text_area(
        "Topic",
        placeholder="e.g. How LangGraph enables stateful multi-agent AI systems",
        height=110,
        label_visibility="collapsed",
    )
    as_of = st.date_input("As-of date", value=date.today())

    gen_images = st.toggle("Generate Images", value=True, help="Generate AI images via OpenAI")

    run_btn = st.button("🚀 Generate Blog", type="primary", use_container_width=True, disabled=not openai_key.strip())

    st.markdown("---")
    st.markdown("**📂 Past Blogs**")

    past_files = list_past_blogs()
    if not past_files:
        st.caption("No saved blogs yet.")
        selected_md_file = None
    else:
        labels: List[str] = []
        file_map: Dict[str, Path] = {}
        for p in past_files[:30]:
            try:
                text = read_md_file(p)
                title = extract_title_from_md(text, p.stem)
            except Exception:
                title = p.stem
            label = f"{title[:35]}…" if len(title) > 35 else title
            labels.append(label)
            file_map[label] = p

        selected = st.radio("", labels, index=0, label_visibility="collapsed")
        selected_md_file = file_map.get(selected)

        if st.button("📂 Load", use_container_width=True):
            if selected_md_file:
                md_text = read_md_file(selected_md_file)
                st.session_state["last_out"] = {
                    "plan": None,
                    "evidence": [],
                    "image_specs": [],
                    "final": md_text,
                }
                st.rerun()


# Hero header

st.markdown("""
<div class="hero">
    <h1>✍️ Agentic Blog Writer</h1>
    <p>Multi-agent AI pipeline · Researches, plans, writes, and illustrates blogs automatically</p>
    <div class="badge-row">
        <span class="badge badge-purple">🔗 LangGraph</span>
        <span class="badge badge-teal">🔍 Tavily Research</span>
        <span class="badge badge-green">💾 SQLite Memory</span>
        <span class="badge badge-amber">🖼️ OpenAI Images</span>
    </div>
</div>
""", unsafe_allow_html=True)


# Run graph 

if run_btn:
    if not openai_key.strip():
        st.error("Please enter your OpenAI API key first.")
        st.stop()
    if not topic.strip():
        st.warning("Please enter a topic first.")
        st.stop()

    # New thread for each run
    st.session_state["thread_id"] = str(uuid.uuid4())
    st.session_state["run_logs"] = []

    inputs: Dict[str, Any] = {
        "topic": topic.strip(),
        "mode": "",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": None,
        "as_of": as_of.isoformat(),
        "recency_days": 7,
        "sections": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
    }

    config = {"configurable": {"thread_id": st.session_state["thread_id"]}}

    NODE_LABELS = {
        "router":      ("🔀", "Router", "Deciding research mode…"),
        "research":    ("🔍", "Research", "Searching the web…"),
        "orchestrator":("🧠", "Orchestrator", "Planning blog structure…"),
        "worker":      ("✍️", "Writer", "Writing sections in parallel…"),
        "reducer":     ("🔧", "Reducer", "Merging & adding images…"),
        "merge_content":       ("📎", "Merge", "Combining sections…"),
        "decide_images":       ("🖼️", "Image Planner", "Deciding where images go…"),
        "generate_and_place_images": ("🎨", "Image Generator", "Generating AI images…"),
    }

    status_box = st.status("🚀 Running agent pipeline…", expanded=True)
    progress_placeholder = st.empty()
    current_state: Dict[str, Any] = {}
    last_node = None

    with status_box:
        for kind, payload in try_stream(app, inputs, config):
            if kind in ("updates", "values"):
                node_name = None
                if isinstance(payload, dict) and len(payload) == 1:
                    node_name = next(iter(payload.keys()))

                if node_name and node_name != last_node:
                    icon, label, desc = NODE_LABELS.get(node_name, ("⚙️", node_name, "Processing…"))
                    st.markdown(
                        f'<div class="node-pill">{icon} <b>{label}</b> — {desc}</div>',
                        unsafe_allow_html=True,
                    )
                    last_node = node_name

                current_state = extract_latest_state(current_state, payload)

                # Live stats
                ev_count = len(current_state.get("evidence", []) or [])
                plan_obj = current_state.get("plan")
                task_count = len(plan_obj.tasks) if hasattr(plan_obj, "tasks") else (
                    len(plan_obj.get("tasks", [])) if isinstance(plan_obj, dict) else 0
                )
                sec_count = len(current_state.get("sections", []) or [])
                img_count = len(current_state.get("image_specs", []) or [])
                mode = current_state.get("mode") or "—"

                progress_placeholder.markdown(f"""
<div class="stat-row">
  <div class="stat-card"><div class="stat-val">{mode}</div><div class="stat-lbl">Mode</div></div>
  <div class="stat-card"><div class="stat-val">{ev_count}</div><div class="stat-lbl">Sources</div></div>
  <div class="stat-card"><div class="stat-val">{task_count}</div><div class="stat-lbl">Sections planned</div></div>
  <div class="stat-card"><div class="stat-val">{sec_count}</div><div class="stat-lbl">Written</div></div>
  <div class="stat-card"><div class="stat-val">{img_count}</div><div class="stat-lbl">Images</div></div>
</div>
""", unsafe_allow_html=True)

                log_entry = f"[{kind}] {node_name or '?'}: {json.dumps(payload, default=str)[:400]}"
                st.session_state["run_logs"].append(log_entry)

            elif kind == "final":
                st.session_state["last_out"] = payload
                st.session_state["run_logs"].append("[final] Pipeline complete ✅")

    status_box.update(label="✅ Blog generated!", state="complete", expanded=False)
    progress_placeholder.empty()
    st.rerun()


# Output tabs 

out = st.session_state.get("last_out")

if out:
    tab_preview, tab_plan, tab_evidence, tab_images, tab_logs = st.tabs([
        "📝 Blog Preview",
        "🧩 Plan",
        "🔎 Sources",
        "🖼️ Images",
        "🧾 Logs",
    ])

    # Blog Preview 
    with tab_preview:
        final_md = out.get("final") or ""
        if not final_md:
            st.info("No blog generated yet. Enter a topic and click Generate.")
        else:
            plan_obj = out.get("plan")
            if hasattr(plan_obj, "blog_title"):
                blog_title = plan_obj.blog_title
            elif isinstance(plan_obj, dict):
                blog_title = plan_obj.get("blog_title", "blog")
            else:
                blog_title = extract_title_from_md(final_md, "blog")

            md_filename = f"{safe_slug(blog_title)}.md"

            # Download buttons
            col1, col2 = st.columns([1, 4])
            with col1:
                st.download_button(
                    "⬇️ Markdown",
                    data=final_md.encode("utf-8"),
                    file_name=md_filename,
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col2:
                bundle = bundle_zip(final_md, md_filename, Path("images"))
                st.download_button(
                    "📦 Download Bundle (MD + Images)",
                    data=bundle,
                    file_name=f"{safe_slug(blog_title)}_bundle.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

            st.markdown("---")
            render_blog_markdown(final_md)

    # Plan 
    with tab_plan:
        plan_obj = out.get("plan")
        if not plan_obj:
            st.info("No plan available.")
        else:
            if hasattr(plan_obj, "model_dump"):
                plan_dict = plan_obj.model_dump()
            elif isinstance(plan_obj, dict):
                plan_dict = plan_obj
            else:
                plan_dict = json.loads(json.dumps(plan_obj, default=str))

            col1, col2, col3 = st.columns(3)
            col1.metric("Audience", plan_dict.get("audience", "—"))
            col2.metric("Tone", plan_dict.get("tone", "—"))
            col3.metric("Blog Kind", plan_dict.get("blog_kind", "—"))

            st.markdown(f"### {plan_dict.get('blog_title', '')}")

            tasks = plan_dict.get("tasks", [])
            if tasks:
                df = pd.DataFrame([{
                    "#": t.get("id"),
                    "Section": t.get("title"),
                    "Target Words": t.get("target_words"),
                    "Research": "✅" if t.get("requires_research") else "—",
                    "Citations": "✅" if t.get("requires_citations") else "—",
                    "Code": "✅" if t.get("requires_code") else "—",
                    "Tags": ", ".join(t.get("tags") or []),
                } for t in tasks]).sort_values("#")
                st.dataframe(df, use_container_width=True, hide_index=True)

                with st.expander("📋 Full task details (JSON)"):
                    st.json(tasks)

    # Evidence / Sources 
    with tab_evidence:
        evidence = out.get("evidence") or []
        if not evidence:
            st.info("No evidence found (closed_book mode or no Tavily API key).")
        else:
            st.markdown(f"**{len(evidence)} sources retrieved**")
            for e in evidence:
                if hasattr(e, "model_dump"):
                    e = e.model_dump()
                title = e.get("title") or "Untitled"
                url = e.get("url") or "#"
                pub = e.get("published_at") or ""
                source = e.get("source") or ""
                snippet = e.get("snippet") or ""

                st.markdown(f"""
<div class="evidence-card">
    <a href="{url}" target="_blank">🔗 {title}</a>
    <div class="ev-meta">{source}{' · ' + pub if pub else ''}</div>
    {"<p style='font-size:0.82rem;color:#6b7280;margin-top:0.3rem'>" + snippet[:200] + "…</p>" if snippet else ""}
</div>
""", unsafe_allow_html=True)

    # Images 
    with tab_images:
        specs = out.get("image_specs") or []
        images_dir = Path("images")

        if not specs and not images_dir.exists():
            st.info("No images generated for this blog.")
        else:
            if specs:
                st.markdown(f"**{len(specs)} image(s) planned**")
                for s in specs:
                    with st.expander(f"🖼️ {s.get('placeholder', '')} — {s.get('filename', '')}"):
                        st.markdown(f"**Alt:** {s.get('alt', '')}")
                        st.markdown(f"**Caption:** {s.get('caption', '')}")
                        st.markdown(f"**Prompt:** `{s.get('prompt', '')}`")

            if images_dir.exists():
                img_files = [p for p in images_dir.iterdir() if p.is_file()]
                if img_files:
                    st.markdown("---")
                    cols = st.columns(min(len(img_files), 2))
                    for idx, p in enumerate(sorted(img_files)):
                        with cols[idx % 2]:
                            st.image(str(p), caption=p.name, use_container_width=True)

    # Logs
    with tab_logs:
        logs = st.session_state.get("run_logs", [])
        if not logs:
            st.info("No logs yet.")
        else:
            log_text = "\n\n".join(logs[-60:])
            st.markdown(f'<div class="log-box"><pre>{log_text}</pre></div>', unsafe_allow_html=True)

else:
    # Empty state
    st.markdown("""
<div style="text-align:center; padding: 4rem 2rem; color: #9ca3af;">
    <div style="font-size: 4rem; margin-bottom: 1rem;">✍️</div>
    <h3 style="color: #374151; font-weight: 600;">Ready to write</h3>
    <p>Enter a topic in the sidebar and click <strong>Generate Blog</strong></p>
    <p style="font-size: 0.85rem;">The agent will research, plan, write, and illustrate your blog automatically.</p>
</div>
""", unsafe_allow_html=True)