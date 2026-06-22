# ✍️ Agentic Blog Writer — LangGraph Multi-Agent System

A production-grade multi-agent blog writing system built with LangGraph. The agent automatically researches, plans, writes, and illustrates technical blogs.

## 🏗️ Architecture

```
User Input (topic)
      ↓
  [Router] → decides: closed_book / hybrid / open_book
      ↓
  [Research] → Tavily web search (if needed)
      ↓
  [Orchestrator] → creates structured Plan (5–9 sections)
      ↓
  [Workers] → parallel section writers (one per task via Send API)
      ↓
  [Reducer Subgraph]
    ├── merge_content    → joins all sections + sources
    ├── decide_images    → plans image placements (max 3)
    └── generate_and_place_images → HuggingFace FLUX / Pollinations fallback
      ↓
  Final Blog (Markdown + images saved locally)
```

## 🔑 Key Features

- **Multi-agent parallel writing** — sections written concurrently via LangGraph `Send` API
- **Smart routing** — decides whether web research is needed before planning
- **Clickable sources** — all citations rendered as inline Markdown links
- **AI image generation** — HuggingFace FLUX.1-dev with Pollinations.ai as automatic fallback
- **In-memory state** — full graph state managed across nodes
- **LangSmith tracing** — full observability of every node and LLM call
- **Graceful fallbacks** — image failures never break the blog output

## 📁 Project Structure

```
blog_writer_agent/
├── app.py              # Streamlit UI
├── graph.py            # LangGraph graph definition
├── schemas.py          # All Pydantic models + State
├── llm.py              # LLM instance (OpenAI)
├── nodes/
│   ├── router.py       # Routing node + route_next
│   ├── research.py     # Tavily research node
│   ├── orchestrator.py # Blog planning node
│   ├── worker.py       # Section writing node
│   └── reducer.py      # Merge + image generation nodes
├── utils/
│   └── helpers.py      # Shared utilities
├── images/             # Generated images saved here
├── requirements.txt
└── .env.example
```

## 🚀 Setup

```bash
# 1. Clone and enter project
git clone <your-repo>
cd blog_writer_agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Fill in your API keys in .env

# 4. Run
streamlit run app.py
```

## 🔑 API Keys Required

| Key | Purpose | Free tier? |
|-----|---------|-----------|
| `OPENAI_API_KEY` | LLM for all text generation | No |
| `TAVILY_API_KEY` | Web research | ✅ Yes (1000 searches/mo) |
| `HF_TOKEN` | HuggingFace FLUX image generation | ✅ Yes |
| `LANGCHAIN_API_KEY` | LangSmith tracing | ✅ Yes |

> **Note:** `HF_TOKEN` is optional. If not set, image generation automatically falls back to Pollinations.ai — completely free, no signup required.

## 💡 Interview Talking Points

- **Fanout pattern** (`Send` API) — parallel section writing, not sequential
- **Reducer subgraph** — separate subgraph for merge/image pipeline
- **Conditional routing** — router decides research mode before any LLM planning
- **Structured outputs** — Pydantic models for every LLM response
- **Provider fallback chain** — HuggingFace FLUX → Pollinations.ai for resilient image generation
- **Graceful fallbacks** — image failures don't break the blog
