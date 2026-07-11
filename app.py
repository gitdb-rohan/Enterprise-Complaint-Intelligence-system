import os, re, traceback
import pandas as pd
import altair as alt
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Enterprise Complaint Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Premium Dark Theme CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0e1a !important;
    font-family: 'Inter', sans-serif !important;
    color: #e2e8f0 !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { display: none; }

/* Main container */
[data-testid="stAppViewContainer"] > .main > div {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Column containers */
[data-testid="column"] { padding: 0 8px !important; }

/* Chart card */
.chart-card {
    background: linear-gradient(135deg, #111827 0%, #1a2235 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 4px 24px rgba(0,100,255,0.08);
}

.chart-card-ai {
    background: linear-gradient(135deg, #0d2137 0%, #1a1a3e 100%);
    border: 1px solid #4c6ef5;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 0 24px rgba(76,110,245,0.2);
}

/* Metric card */
.metric-row {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
}
.metric-card {
    flex: 1;
    background: linear-gradient(135deg, #1a2235 0%, #111827 100%);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
}
.metric-label { font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { font-size: 26px; font-weight: 700; color: #60a5fa; margin-top: 4px; }

/* Section header */
.section-header {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 16px 0 8px 0;
    padding-left: 4px;
}

/* AI badge */
.ai-badge {
    display: inline-block;
    background: linear-gradient(90deg, #4c6ef5, #7c3aed);
    color: white;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
}

/* Chat panel */
.chat-header {
    background: linear-gradient(135deg, #111827 0%, #1a2235 100%);
    border-bottom: 1px solid #1e3a5f;
    padding: 16px 20px;
    border-radius: 12px 12px 0 0;
    margin-bottom: 0;
}
.chat-panel {
    background: #0f1623;
    border: 1px solid #1e3a5f;
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 12px;
    height: calc(100vh - 220px);
    overflow-y: auto;
}

/* Suggested question pills */
.pill-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }

/* User bubble */
.user-bubble {
    background: linear-gradient(135deg, #1e40af, #4c6ef5);
    color: white;
    border-radius: 16px 16px 4px 16px;
    padding: 10px 14px;
    margin: 6px 0 6px 20%;
    font-size: 13px;
    line-height: 1.5;
}

/* AI bubble */
.ai-bubble {
    background: linear-gradient(135deg, #111827, #1a2235);
    border: 1px solid #1e3a5f;
    color: #e2e8f0;
    border-radius: 4px 16px 16px 16px;
    padding: 10px 14px;
    margin: 6px 20% 6px 0;
    font-size: 13px;
    line-height: 1.5;
}

/* Divider */
.panel-divider {
    width: 1px;
    background: linear-gradient(to bottom, transparent, #1e3a5f, transparent);
}

/* Streamlit overrides */
div[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 4px 0 !important;
}
div[data-testid="stChatInput"] textarea {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 13px !important;
}
div[data-testid="stChatInput"] textarea:focus {
    border-color: #4c6ef5 !important;
    box-shadow: 0 0 0 2px rgba(76,110,245,0.2) !important;
}

button[kind="secondary"] {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    color: #93c5fd !important;
    border-radius: 20px !important;
    font-size: 11px !important;
    padding: 4px 12px !important;
}
button[kind="secondary"]:hover {
    background: #1e3a5f !important;
    border-color: #4c6ef5 !important;
}

/* Vega chart background */
.vega-embed { background: transparent !important; }
.vega-embed canvas { border-radius: 8px; }

/* App title bar */
.app-title {
    padding: 14px 20px;
    background: linear-gradient(90deg, #0d1117 0%, #111827 100%);
    border-bottom: 1px solid #1e3a5f;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0;
}
.app-title h1 {
    font-size: 18px;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0;
    background: linear-gradient(90deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.app-title .subtitle {
    font-size: 12px;
    color: #4b5563;
}

hr { border-color: #1e3a5f !important; }
</style>
""", unsafe_allow_html=True)

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found in .env")
    st.stop()

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_parquet("portfolio_data.parquet")
    df["date_received"] = pd.to_datetime(df["date_received"], utc=True)
    return df

df = load_data()

# ── Session State ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ai_charts" not in st.session_state:
    st.session_state.ai_charts = []   # list of {title, chart, question}
if "pending_q" not in st.session_state:
    st.session_state.pending_q = None

# ── Gemini prompt setup ───────────────────────────────────────────────────────
SCHEMA = """
DataFrame `df` — 1,807 rows of consumer financial complaints.

Columns:
- date_received          : datetime (UTC) — when complaint was filed
- product                : str — e.g. "Student loan", "Credit reporting..."
- sub-product            : str (access as df["sub-product"])
- issue                  : str
- sub-issue              : str (access as df["sub-issue"])
- company                : str — e.g. "MOHELA"
- state                  : str — 2-letter US state
- zip_code               : str
- submitted_via          : str — "Web", "Phone", etc.
- company_response_to_consumer : str — "Closed with explanation", "In progress", etc.
- timely_response?       : str — "Yes" or "No" (access as df["timely_response?"])
- complaint_id           : float64

Notes:
- Use df["sub-product"], df["sub-issue"], df["timely_response?"] for hyphenated/punctuated names
- date_received is already datetime — .dt accessor works
- For month grouping: df["date_received"].dt.to_period("M").astype(str)
"""

SYSTEM_PROMPT = f"""You are a Python data analyst embedded in a financial complaint analytics dashboard.

Dataset schema:
{SCHEMA}

Instructions:
1. Write pandas + altair code to answer the user's question.
2. Assign the final Altair chart to variable `chart`. Use dark-friendly colors from this palette: ['#60a5fa','#a78bfa','#34d399','#f87171','#fbbf24','#38bdf8'].
3. Make charts visually clear with proper titles, axis labels, and tooltips.
4. Configure charts with: .configure_view(strokeWidth=0).configure_axis(gridColor='#1e3a5f', labelColor='#9ca3af', titleColor='#6b7280').configure_title(color='#e2e8f0')
5. If chart is not appropriate, set chart = None.
6. Wrap ALL code in ```python ... ``` block.
7. After the code block, write: EXPLANATION: <your plain-English insight about what the data shows>
8. Keep explanations concise (2-4 sentences), data-driven, and actionable.
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
def extract_code_and_explanation(text):
    code_match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    code = code_match.group(1).strip() if code_match else None
    exp_match = re.search(r"EXPLANATION:\s*(.*?)$", text, re.DOTALL)
    explanation = exp_match.group(1).strip() if exp_match else text.strip()
    return code, explanation

def run_code(code):
    ns = {"df": df.copy(), "pd": pd, "alt": alt, "chart": None}
    try:
        exec(code, ns)  # noqa: S102
        return ns.get("chart"), None
    except Exception:
        return None, traceback.format_exc()

def stream_words(text):
    for word in text.split():
        yield word + " "

# ── Default Charts ────────────────────────────────────────────────────────────
CHART_CFG = dict(strokeWidth=0)
AXIS_CFG = dict(gridColor='#1e3a5f', labelColor='#9ca3af', titleColor='#6b7280', domainColor='#1e3a5f')
TITLE_CFG = dict(color='#e2e8f0', fontSize=13, fontWeight=600)
COLORS = ['#60a5fa','#a78bfa','#34d399','#f87171','#fbbf24','#38bdf8','#fb923c','#4ade80']

@st.cache_data
def build_default_charts():
    charts = {}

    # 1. Top 10 Products
    prod = df['product'].value_counts().reset_index().head(10)
    prod.columns = ['Product', 'Count']
    charts['products'] = (
        alt.Chart(prod).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y('Product:N', sort='-x', axis=alt.Axis(labelLimit=200)),
            x=alt.X('Count:Q', title='Complaints'),
            color=alt.value('#60a5fa'),
            tooltip=['Product','Count']
        )
        .properties(title='Top 10 Products', height=260)
        .configure_view(strokeWidth=0)
        .configure_axis(**AXIS_CFG)
        .configure_title(**TITLE_CFG)
    )

    # 2. Top 10 Companies
    comp = df['company'].value_counts().reset_index().head(10)
    comp.columns = ['Company', 'Count']
    charts['companies'] = (
        alt.Chart(comp).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y('Company:N', sort='-x', axis=alt.Axis(labelLimit=200)),
            x=alt.X('Count:Q', title='Complaints'),
            color=alt.value('#a78bfa'),
            tooltip=['Company','Count']
        )
        .properties(title='Top 10 Companies', height=260)
        .configure_view(strokeWidth=0)
        .configure_axis(**AXIS_CFG)
        .configure_title(**TITLE_CFG)
    )

    # 3. Monthly Trend
    df2 = df.copy()
    df2['month'] = df2['date_received'].dt.to_period('M').astype(str)
    trend = df2.groupby('month').size().reset_index(name='Count')
    charts['trend'] = (
        alt.Chart(trend).mark_area(
            line={'color':'#34d399'}, color=alt.Gradient(
                gradient='linear', stops=[
                    alt.GradientStop(color='rgba(52,211,153,0.3)', offset=0),
                    alt.GradientStop(color='rgba(52,211,153,0)', offset=1)
                ], x1=1, x2=1, y1=1, y2=0
            )
        )
        .encode(
            x=alt.X('month:T', title='Month'),
            y=alt.Y('Count:Q', title='Complaints'),
            tooltip=['month','Count']
        )
        .properties(title='Monthly Complaint Trend', height=180)
        .configure_view(strokeWidth=0)
        .configure_axis(**AXIS_CFG)
        .configure_title(**TITLE_CFG)
    )

    # 4. Top 15 States
    states = df['state'].value_counts().reset_index().head(15)
    states.columns = ['State','Count']
    charts['states'] = (
        alt.Chart(states).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X('State:N', sort='-y'),
            y=alt.Y('Count:Q', title='Complaints'),
            color=alt.Color('Count:Q', scale=alt.Scale(scheme='blues'), legend=None),
            tooltip=['State','Count']
        )
        .properties(title='Top 15 States', height=200)
        .configure_view(strokeWidth=0)
        .configure_axis(**AXIS_CFG)
        .configure_title(**TITLE_CFG)
    )

    # 5. Response type donut
    resp = df['company_response_to_consumer'].value_counts().reset_index().head(6)
    resp.columns = ['Response','Count']
    charts['response'] = (
        alt.Chart(resp).mark_arc(innerRadius=50, cornerRadius=4)
        .encode(
            theta=alt.Theta('Count:Q'),
            color=alt.Color('Response:N', scale=alt.Scale(range=COLORS), legend=alt.Legend(labelColor='#9ca3af', titleColor='#6b7280')),
            tooltip=['Response','Count']
        )
        .properties(title='Company Response Types', height=220)
        .configure_view(strokeWidth=0)
        .configure_title(**TITLE_CFG)
    )

    # 6. Submission channel
    channels = df['submitted_via'].value_counts().reset_index()
    channels.columns = ['Channel','Count']
    charts['channels'] = (
        alt.Chart(channels).mark_arc(innerRadius=40, cornerRadius=4)
        .encode(
            theta=alt.Theta('Count:Q'),
            color=alt.Color('Channel:N', scale=alt.Scale(range=COLORS), legend=alt.Legend(labelColor='#9ca3af', titleColor='#6b7280')),
            tooltip=['Channel','Count']
        )
        .properties(title='Submission Channels', height=220)
        .configure_view(strokeWidth=0)
        .configure_title(**TITLE_CFG)
    )

    return charts

default_charts = build_default_charts()

# ── App Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-title">
  <div>
    <h1>🏦 Enterprise Complaint Intelligence</h1>
    <div class="subtitle">1,807 consumer financial complaints · Powered by Gemini AI</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Metrics Row ───────────────────────────────────────────────────────────────
timely_pct = round(df["timely_response?"].eq("Yes").mean() * 100, 1)
m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("Total Complaints", f"{len(df):,}")
with m2: st.metric("Unique Products", df['product'].nunique())
with m3: st.metric("Unique Companies", df['company'].nunique())
with m4: st.metric("States Covered", df['state'].nunique())
with m5: st.metric("Timely Response", f"{timely_pct}%")

st.markdown("<hr style='margin:8px 0 16px 0;'>", unsafe_allow_html=True)

# ── Main Split Layout ─────────────────────────────────────────────────────────
left, right = st.columns([6, 4], gap="medium")

# ═══════════════════════════════════════════════════════════════════
# LEFT PANEL: Charts
# ═══════════════════════════════════════════════════════════════════
with left:
    # AI-generated charts (newest first)
    if st.session_state.ai_charts:
        st.markdown('<div class="section-header">🤖 AI Generated Charts</div>', unsafe_allow_html=True)
        for item in reversed(st.session_state.ai_charts):
            st.markdown(f'<div class="ai-badge">✨ AI · {item["question"][:60]}{"..." if len(item["question"])>60 else ""}</div>', unsafe_allow_html=True)
            st.altair_chart(item["chart"], use_container_width=True)
            st.markdown("<hr style='margin:4px 0 12px 0;'>", unsafe_allow_html=True)

    # Default charts
    st.markdown('<div class="section-header">📊 Dashboard Overview</div>', unsafe_allow_html=True)

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.altair_chart(default_charts['products'], use_container_width=True)
    with r1c2:
        st.altair_chart(default_charts['companies'], use_container_width=True)

    st.altair_chart(default_charts['trend'], use_container_width=True)
    st.altair_chart(default_charts['states'], use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.altair_chart(default_charts['response'], use_container_width=True)
    with r2c2:
        st.altair_chart(default_charts['channels'], use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# RIGHT PANEL: AI Chat
# ═══════════════════════════════════════════════════════════════════
with right:
    st.markdown("""
    <div class="chat-header">
      <div style="font-size:15px;font-weight:600;color:#e2e8f0;">🤖 AI Data Analyst</div>
      <div style="font-size:11px;color:#4b5563;margin-top:2px;">Ask anything about the dataset</div>
    </div>
    """, unsafe_allow_html=True)

    # Suggested questions
    SUGGESTIONS = [
        "Which state has most complaints?",
        "Top 5 issues for student loans?",
        "Monthly trend for MOHELA?",
        "Timely response breakdown?",
        "Compare Web vs Phone submissions",
        "Which company has most unresolved cases?",
    ]

    st.markdown('<div style="padding:8px 0 4px 0;">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(q, key=f"sq_{i}", use_container_width=True):
                st.session_state.pending_q = q
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

    # Chat history
    chat_container = st.container(height=480)
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align:center;padding:32px 16px;color:#4b5563;">
              <div style="font-size:32px;margin-bottom:8px;">💬</div>
              <div style="font-size:13px;">Ask a question above or click a suggestion<br>to generate insights and charts.</div>
            </div>
            """, unsafe_allow_html=True)
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask about the data…")

    # Process pending (suggested) or typed question
    question = st.session_state.pop("pending_q", None) or user_input

    if question:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": question})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(question)

        # Generate
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {question}"
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Analysing…"):
                    try:
                        raw = ai_client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=full_prompt
                        )
                        response_text = raw.text
                        code, explanation = extract_code_and_explanation(response_text)

                        chart_obj = None
                        if code:
                            chart_obj, exec_err = run_code(code)
                            if exec_err:
                                explanation = "I had trouble generating a chart for that. " + explanation

                        # Store chart in left panel
                        if chart_obj is not None:
                            st.session_state.ai_charts.append({
                                "question": question,
                                "chart": chart_obj
                            })

                        # Stream explanation
                        streamed = st.write_stream(stream_words(explanation))
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": streamed if isinstance(streamed, str) else explanation
                        })

                        if chart_obj is not None:
                            st.info("📊 Chart added to the left panel!", icon="✅")

                        st.rerun()

                    except ClientError as ce:
                        if "RESOURCE_EXHAUSTED" in str(ce):
                            msg = "⚠️ Rate limit hit. Please wait ~60 seconds and try again."
                        else:
                            msg = f"Gemini API error: {ce}"
                        st.error(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                    except Exception as e:
                        msg = f"Error: {e}"
                        st.error(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})

    # Clear chat
    if st.session_state.messages:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.ai_charts = []
            st.rerun()
