# 🏦 Enterprise Complaint Intelligence

A full-stack AI-powered analytics platform for exploring and querying **CFPB (Consumer Financial Protection Bureau)** consumer complaints. Built with **Google Gemini**, **ChromaDB**, **Streamlit**, and **MCP** (Model Context Protocol).

---

## 📸 What It Looks Like

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🏦 Enterprise Complaint Intelligence     [Total] [Products] [Companies] ...  │
├─────────────────────────────────────────┬────────────────────────────────────┤
│  📊 CHARTS PANEL (live, grows as you   │  🤖 AI DATA ANALYST                │
│  ask questions)                         │                                    │
│                                         │  [Suggested question pills]        │
│  ✨ AI Badge — your question here       │                                    │
│  [Dynamically generated chart]  ←───── │  ────────────────────────────────  │
│  ─────────────────────────────          │                                    │
│  Top Products    │  Top Companies       │  Chat history (scrollable)         │
│  Monthly Trend (area chart)             │                                    │
│  Top 15 States (bar chart)              │                                    │
│  Response Types  │  Submission Channels │  [Ask about the data…  ⏎]         │
└─────────────────────────────────────────┴────────────────────────────────────┘
```

- **Left panel (60%)** — Static overview dashboard + AI-generated charts that accumulate as you ask questions
- **Right panel (40%)** — Persistent AI chat with 6 one-click suggested questions and streamed explanations

---

## 🧠 Architecture Overview

```
                        ┌──────────────────────────────────────┐
                        │        CFPB Public REST API          │
                        └──────────────┬───────────────────────┘
                                       │ data_fetch.py / bypass_fetch.py
                                       ▼
                        ┌──────────────────────────────────────┐
                        │    complaints_sample_2000.csv        │
                        │    (2,000 raw complaint records)     │
                        └──────────────┬───────────────────────┘
                                       │ prepare_data.py
                       ┌───────────────┴─────────────────┐
                       ▼                                 ▼
          ┌─────────────────────┐           ┌──────────────────────────┐
          │ processed_complaints│           │  portfolio_data.parquet   │
          │   .parquet          │           │  (1,807 records without  │
          │  (193 with          │           │   narratives — analytics)│
          │   narratives — RAG) │           └───────────────┬──────────┘
          └────────────┬────────┘                           │
                       │ embed.py                           │
                       ▼                                    │
          ┌────────────────────────┐                        │
          │  ChromaDB (local)      │                        │
          │  complaint_db/         │                        │
          │  Gemini text-embedding │                        │
          └──────────────┬─────────┘                        │
                         │                                  │
                         └────────────────┬─────────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │       app.py  (Streamlit)     │
                          │  ┌─────────────┬───────────┐  │
                          │  │ Charts Panel│ AI Chat   │  │
                          │  │             │           │  │
                          │  │  Static     │ Gemini    │  │
                          │  │  charts     │ 2.0-flash │  │
                          │  │  +          │ code-gen  │  │
                          │  │  AI charts  │ + stream  │  │
                          │  └─────────────┴───────────┘  │
                          └───────────────────────────────┘
                                          │
                          ┌───────────────┴──────────────┐
                          │    mcp_server.py (FastMCP)   │
                          │  Tools: search_complaints,   │
                          │         get_portfolio_stats  │
                          └──────────────────────────────┘
```

---

## 📁 Project File Reference

| File | Purpose |
|------|---------|
| `app.py` | **Main entry point.** Single-page Streamlit app with split-screen layout: charts on the left, AI chat on the right. |
| `data_fetch.py` | Fetches complaint data from the CFPB public REST API with retry logic, saves raw CSV. |
| `bypass_fetch.py` | Alternative fetcher — bypasses API rate limits using direct HTTP with retries. |
| `prepare_data.py` | Splits raw `complaints_sample_2000.csv` into two Parquet files: one for RAG (with narratives) and one for analytics (without). |
| `embed.py` | Reads `processed_complaints.parquet`, embeds narratives using **Gemini text-embedding**, stores them in local **ChromaDB**. |
| `data_analysys.py` | Standalone exploratory analysis script (used during development). |
| `mcp_server.py` | **MCP Server** using FastMCP. Exposes ChromaDB and portfolio data as AI tools for external clients. |
| `process.ipynb` | Jupyter notebook used for prototyping the data pipeline. |
| `portfolio_data.parquet` | 1,807 complaints without narratives — powers the analytics dashboard. |
| `processed_complaints.parquet` | 193 complaints with full narratives — indexed into ChromaDB for RAG. |
| `complaints_sample_2000.csv` | Raw 2,000-record sample from CFPB API. |
| `complaint_db/` | Local ChromaDB vector store (auto-created by `embed.py`). |
| `.env` | Stores your `GEMINI_API_KEY`. Never commit this to Git. |
| `pyproject.toml` | Python project config and dependencies (managed by `uv`). |

---

## ⚙️ How Each Pipeline Stage Works

### Stage 1 — Data Fetching
## data is from -- https://www.consumerfinance.gov
```bash
uv run python data_fetch.py
# OR if API is unreliable:
uv run python bypass_fetch.py
```
Pulls up to 2,000 complaints from `https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/` using paginated requests with exponential retry. Saves to `complaints_sample_2000.csv`.

---

### Stage 2 — Data Preprocessing
```bash
uv run python prepare_data.py
```
Reads the raw CSV and:
- Filters rows **with** a complaint narrative → `processed_complaints.parquet` (RAG dataset, ~193 rows)
- Keeps rows **without** a narrative → `portfolio_data.parquet` (analytics dataset, ~1,807 rows)

---

### Stage 3 — Vector Embedding (RAG Indexing)
```bash
uv run python embed.py
```
- Reads `processed_complaints.parquet`
- Calls **Gemini Embedding API** (`models/embedding-001`) on each narrative (batched in groups of 50 with rate-limit sleeps)
- Stores all vectors + metadata in local **ChromaDB** at `./complaint_db/`

> ⚠️ Free-tier Gemini API allows ~100 embed requests/minute. The script auto-sleeps 15s between batches.

---

### Stage 4 — Run the App
```bash
uv run streamlit run app.py
```
Opens the full split-screen dashboard at **http://localhost:8501**

---

## 🤖 AI Features Deep Dive

### Dynamic Chart Generation (Left Panel)
When you ask a question in the chat:
1. Your question + the full DataFrame schema is sent to **Gemini 2.0 Flash**
2. Gemini writes pandas + altair Python code specifically to answer your question
3. The code runs locally against `portfolio_data.parquet` in a sandboxed `exec()` environment
4. The resulting Altair chart appears at the **top of the left panel** with a purple `✨ AI` badge
5. Explanation streams word-by-word into the chat bubble

Charts accumulate as you ask more questions — giving you a live, evolving dashboard.

### Suggested Questions (One-click)
Six pre-configured question pills in the chat panel:
- *"Which state has most complaints?"*
- *"Top 5 issues for student loans?"*
- *"Monthly trend for MOHELA?"*
- *"Timely response breakdown?"*
- *"Compare Web vs Phone submissions"*
- *"Which company has most unresolved cases?"*

Click any pill → question fires automatically, chart + explanation generated.

### RAG Chatbot (via ChromaDB)
The embedded narratives in `complaint_db/` power semantic search:
- Query is embedded with Gemini
- Top-5 closest complaint narratives retrieved
- Gemini 2.0 Flash synthesizes a structured analysis: **Severity Level**, **Root Cause Theme**, **Recommended Action**
- Response streams live

### MCP Server (External Tool Access)
```bash
uv run mcp dev mcp_server.py
```
Exposes two tools to any MCP-compatible client (Claude Desktop, etc.):

| Tool | Description |
|------|-------------|
| `search_complaints` | Semantic search against ChromaDB vector store |
| `get_portfolio_stats` | Returns aggregated metrics from portfolio Parquet |

---

## 📊 Dataset Details

**Source**: [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/)

| Attribute | Value |
|-----------|-------|
| Total records sampled | 2,000 |
| Records with narratives (RAG) | ~193 |
| Records without narratives (Analytics) | ~1,807 |
| Date range | 2024–2025 |
| Key companies | MOHELA, TransUnion, Equifax, etc. |
| Key products | Student loans, Credit reporting, Mortgages |

---

## 🚀 Quickstart

### Prerequisites
- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) package manager
- A **Gemini API key** from [Google AI Studio](https://aistudio.google.com)

### Setup
```bash
# 1. Clone and enter project
cd interview

# 2. Install dependencies
uv sync

# 3. Add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env

# 4. (First run only) Fetch data and build vector index
uv run python data_fetch.py
uv run python prepare_data.py
uv run python embed.py

# 5. Launch the app
uv run streamlit run app.py
```

Open **http://localhost:8501** 🎉

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Your Google Gemini API key from AI Studio |

---

## 🛠️ Tech Stack

| Technology | Role |
|------------|------|
| [Google Gemini 2.0 Flash](https://ai.google.dev) | LLM for code generation, streaming, analysis |
| [Gemini Embedding (models/embedding-001)](https://ai.google.dev) | Text vectorization for semantic search |
| [ChromaDB](https://www.trychroma.com) | Local persistent vector database |
| [Streamlit](https://streamlit.io) | Web application framework |
| [Altair](https://altair-viz.github.io) | Declarative data visualization |
| [Pandas](https://pandas.pydata.org) | DataFrame processing |
| [FastMCP](https://github.com/jlowin/fastmcp) | Model Context Protocol server |
| [uv](https://docs.astral.sh/uv/) | Python package manager |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |

---

## ⚠️ Known Limitations

- **Free-tier rate limits**: Gemini free tier allows ~100 embed requests/min and ~15 chat requests/min. The app gracefully shows a retry message when limits are hit.
- **Small RAG corpus**: Only ~193 narratives are indexed (those with text). The portfolio analytics cover all 1,807 records.
- **Local ChromaDB**: The vector store is local to your machine. Moving to a remote ChromaDB cluster would make this production-ready.

---

## 📝 License

MIT License — free to use, modify, and distribute.
