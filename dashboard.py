import streamlit as st
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

BUNDLER_NAMES = {
    "0xce54f65abb8b61b83c14cbe97de97fce75bbf556": "Pimlico",
    "0x81e3add2b2b6ee38558c8c5a347d4f79e7aeb98e": "Alchemy",
    "0x4337000c2828f5260d8921fd25829f606b9e8680": "Candide",
    "0x3e8e9423d80e1774a7ca128fcb70cd6283b8042e": "Stackup",
    "0xc2b7b9b6f87735625a7c3e3e1b87c2c4f88c7c51": "Biconomy",
}

st.set_page_config(
    page_title="ERC-4337 Bundler Monitor",
    page_icon="https://raw.githubusercontent.com/Operant7-lang/erc4337-bundler-monitor/main/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Inter:wght@300;400;500;600;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #000000;
    font-family: 'Inter', sans-serif;
    overflow-x: hidden;
}

header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] { padding: 0 !important; }

/* ── SCANLINE ── */
body::before {
    content: '';
    position: fixed;
    top: -100%;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(transparent, rgba(204,0,0,0.4), transparent);
    animation: scanline 6s linear infinite;
    z-index: 9999;
    pointer-events: none;
}

@keyframes scanline {
    0%   { top: -2px; }
    100% { top: 100vh; }
}

/* ── GRID BACKGROUND ── */
body::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(204,0,0,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(204,0,0,0.04) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
}

/* ── CORNER DECORATIONS ── */
.corner-tl, .corner-br {
    position: fixed;
    width: 60px;
    height: 60px;
    pointer-events: none;
    z-index: 100;
}
.corner-tl {
    top: 0; left: 0;
    border-top: 2px solid #cc0000;
    border-left: 2px solid #cc0000;
}
.corner-br {
    bottom: 0; right: 0;
    border-bottom: 2px solid #cc0000;
    border-right: 2px solid #cc0000;
}

/* ── NAV ── */
.nav {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 64px;
    background: rgba(0,0,0,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(204,0,0,0.2);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 3rem;
    z-index: 1000;
}

.nav-brand {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.nav-accent {
    width: 4px;
    height: 20px;
    background: #cc0000;
    box-shadow: 0 0 8px #cc0000;
    animation: pulse-bar 2s ease-in-out infinite;
}

@keyframes pulse-bar {
    0%, 100% { box-shadow: 0 0 4px #cc0000; }
    50% { box-shadow: 0 0 16px #cc0000, 0 0 30px rgba(204,0,0,0.3); }
}

.nav-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    color: #cc0000;
    letter-spacing: 0.15em;
}

.nav-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #cc0000;
    box-shadow: 0 0 6px #cc0000;
    animation: blink 1.5s ease-in-out infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.2; }
}

/* ── MAIN CONTENT ── */
.page {
    position: relative;
    z-index: 1;
    padding: 100px 3rem 3rem;
    max-width: 1400px;
    margin: 0 auto;
}

/* ── HERO ── */
.hero {
    padding: 4rem 0 3rem;
    border-bottom: 1px solid rgba(204,0,0,0.15);
    margin-bottom: 3rem;
    animation: fadeUp 0.8s ease forwards;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}

.hero-tag {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #cc0000;
    margin-bottom: 1.2rem;
}

.hero-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: clamp(2.5rem, 6vw, 5rem);
    font-weight: 700;
    line-height: 1.05;
    color: #ffffff;
    margin-bottom: 1.5rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
}

.hero-title .red { color: #cc0000; text-shadow: 0 0 20px rgba(204,0,0,0.4); }

.hero-sub {
    font-size: 0.95rem;
    color: #555;
    max-width: 580px;
    line-height: 1.8;
    font-weight: 300;
}

/* ── STAT GRID ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: rgba(204,0,0,0.1);
    border: 1px solid rgba(204,0,0,0.15);
    margin-bottom: 1px;
    animation: fadeUp 0.8s ease 0.2s both;
}

.stat-cell {
    background: #080808;
    padding: 2rem 2rem;
    position: relative;
    overflow: hidden;
    cursor: default;
    transition: background 0.3s;
}

.stat-cell::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, #cc0000, transparent);
    transform: translateX(-100%);
    transition: transform 0.5s;
}

.stat-cell:hover { background: #0d0000; }
.stat-cell:hover::before { transform: translateX(100%); }

.stat-index {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    color: #333;
    letter-spacing: 0.1em;
    margin-bottom: 0.75rem;
}

.stat-label {
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 0.75rem;
}

.stat-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 3rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
    margin-bottom: 0.5rem;
}

.stat-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #cc0000;
    letter-spacing: 0.1em;
}

/* ── CHART GRID ── */
.chart-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: rgba(204,0,0,0.1);
    border: 1px solid rgba(204,0,0,0.15);
    margin-bottom: 1px;
    animation: fadeUp 0.8s ease 0.4s both;
}

.panel {
    background: #080808;
    padding: 2rem;
}

.panel-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #444;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(204,0,0,0.1);
    margin-bottom: 1.5rem;
}

/* ── ALERT ── */
.alert {
    display: flex;
    align-items: flex-start;
    gap: 1.25rem;
    padding: 1.5rem 2rem;
    border: 1px solid rgba(204,0,0,0.15);
    background: #080808;
    margin-bottom: 1px;
    animation: fadeUp 0.8s ease 0.6s both;
}

.alert-bar {
    width: 3px;
    min-height: 48px;
    flex-shrink: 0;
    margin-top: 2px;
}

.alert-head {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}

.alert-body {
    font-size: 0.85rem;
    color: #555;
    line-height: 1.6;
}

/* ── TABLE ── */
.data-panel {
    background: #080808;
    border: 1px solid rgba(204,0,0,0.15);
    margin-bottom: 1px;
    animation: fadeUp 0.8s ease 0.7s both;
}

.data-panel-header {
    padding: 1.25rem 2rem;
    border-bottom: 1px solid rgba(204,0,0,0.1);
}

/* ── AI SECTION ── */
.ai-panel {
    background: #080808;
    border: 1px solid rgba(204,0,0,0.15);
    padding: 2rem;
    margin-bottom: 1px;
    animation: fadeUp 0.8s ease 0.8s both;
}

.ai-response {
    background: #0d0000;
    border-left: 3px solid #cc0000;
    padding: 1.25rem 1.5rem;
    margin-top: 1.25rem;
    font-size: 0.9rem;
    color: #ccc;
    line-height: 1.8;
    font-family: 'Inter', sans-serif;
}

/* ── FOOTER ── */
.footer {
    border-top: 1px solid rgba(204,0,0,0.1);
    padding-top: 2rem;
    margin-top: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    animation: fadeUp 0.8s ease 0.9s both;
}

.footer-left {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #333;
    letter-spacing: 0.08em;
}

.footer-right a {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #cc0000;
    text-decoration: none;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

/* Override Streamlit elements */
[data-testid="metric-container"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

.stTextInput > div > div > input {
    background: #0d0000 !important;
    border: 1px solid rgba(204,0,0,0.3) !important;
    border-radius: 2px !important;
    color: #ccc !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.85rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #cc0000 !important;
    box-shadow: 0 0 0 1px rgba(204,0,0,0.3) !important;
}

.stDataFrame { border: none !important; }

div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
</style>
""", unsafe_allow_html=True)

# Corner decorations + nav
st.markdown("""
<div class="corner-tl"></div>
<div class="corner-br"></div>
<div class="nav">
    <div class="nav-brand">
        <div class="nav-accent"></div>
        ERC-4337 Bundler Monitor
    </div>
    <div class="nav-status">
        <div class="nav-dot"></div>
        LIVE / ETHEREUM MAINNET
    </div>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    conn = psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        port=os.getenv("SUPABASE_PORT"),
        dbname=os.getenv("SUPABASE_DB"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD")
    )
    df = pd.read_sql("SELECT * FROM userops ORDER BY blocktimestamp DESC", conn)
    conn.close()
    return df

df = load_data()
df['time'] = pd.to_datetime(df['blocktimestamp'], unit='s')
df['bundler_name'] = df['bundler'].str.lower().map(
    {k.lower(): v for k, v in BUNDLER_NAMES.items()}
).fillna(df['bundler'].str[:10] + "...")

bundler_stats = df.groupby('bundler_name').agg(
    total_userops=('userophash', 'count'),
    first_seen=('time', 'min'),
    last_seen=('time', 'max')
).reset_index().sort_values('total_userops', ascending=False)
bundler_stats['market_share'] = (bundler_stats['total_userops'] / len(df) * 100).round(1)

top1_share = float(bundler_stats.head(1)['market_share'].values[0])
top1_name = bundler_stats.head(1)['bundler_name'].values[0]
top3_share = float(bundler_stats.head(3)['market_share'].sum())

# Page wrapper
st.markdown('<div class="page">', unsafe_allow_html=True)

# Hero
st.markdown(f"""
<div class="hero">
    <div class="hero-tag">// Independent Research Tool / Ethereum Mainnet</div>
    <div class="hero-title">
        Who Controls<br>
        <span class="red">Your Transactions?</span>
    </div>
    <div class="hero-sub">
        ERC-4337 smart wallet transactions pass through bundlers before reaching Ethereum.
        This tool monitors whether bundlers treat all transactions fairly —
        or manipulate ordering for profit.
    </div>
</div>
""", unsafe_allow_html=True)

# Stats
st.markdown(f"""
<div class="stat-grid">
    <div class="stat-cell">
        <div class="stat-index">// 01</div>
        <div class="stat-label">UserOps Analyzed</div>
        <div class="stat-value">{len(df):,}</div>
        <div class="stat-sub">from ethereum mainnet</div>
    </div>
    <div class="stat-cell">
        <div class="stat-index">// 02</div>
        <div class="stat-label">Bundlers Tracked</div>
        <div class="stat-value">{df['bundler'].nunique()}</div>
        <div class="stat-sub">active on-chain</div>
    </div>
    <div class="stat-cell">
        <div class="stat-index">// 03</div>
        <div class="stat-label">Unique Senders</div>
        <div class="stat-value">{df['sender'].nunique():,}</div>
        <div class="stat-sub">smart wallet users</div>
    </div>
    <div class="stat-cell">
        <div class="stat-index">// 04</div>
        <div class="stat-label">Top Bundler Share</div>
        <div class="stat-value">{top1_share}%</div>
        <div class="stat-sub">{top1_name.lower()}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Charts
st.markdown('<div class="chart-grid">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="panel"><div class="panel-title">// Bundler Market Share</div>', unsafe_allow_html=True)
    top10 = bundler_stats.head(10).set_index('bundler_name')['total_userops']
    st.bar_chart(top10, height=260, color="#cc0000")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="panel"><div class="panel-title">// Bundler Rankings</div>', unsafe_allow_html=True)
    display = bundler_stats[['bundler_name', 'total_userops', 'market_share']].head(10).copy()
    display.columns = ['Bundler', 'UserOps', 'Share %']
    st.dataframe(display.reset_index(drop=True), use_container_width=True, height=260)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Timeline
st.markdown("""
<div style="background:#080808; border:1px solid rgba(204,0,0,0.15); border-top:none; padding:2rem; margin-bottom:1px;">
    <div class="panel-title">// Activity Timeline</div>
""", unsafe_allow_html=True)
timeline = df.groupby(df['time'].dt.floor('30min')).size().reset_index()
timeline.columns = ['Time', 'UserOps']
st.line_chart(timeline.set_index('Time'), height=160, color="#cc0000")
st.markdown('</div>', unsafe_allow_html=True)

# Alert
alert_color = "#cc0000" if top1_share > 40 else "#00cc44"
alert_bg = "#0d0000" if top1_share > 40 else "#000d00"
alert_title = "CONCENTRATION RISK DETECTED" if top1_share > 40 else "HEALTHY DISTRIBUTION"
alert_msg = f"{top1_name} controls {top1_share}% of all UserOps. Top 3 bundlers combined: {top3_share:.1f}%. Significant centralization detected." if top1_share > 40 else f"No single bundler controls more than 40% of UserOps. Top 3 combined: {top3_share:.1f}% across {len(bundler_stats)} active bundlers."

st.markdown(f"""
<div class="alert" style="background:{alert_bg}; border-color:rgba({','.join(['204,0,0' if top1_share > 40 else '0,204,68'])},0.2);">
    <div class="alert-bar" style="background:{alert_color}; box-shadow: 0 0 8px {alert_color};"></div>
    <div>
        <div class="alert-head" style="color:{alert_color};">{alert_title}</div>
        <div class="alert-body">{alert_msg}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Recent UserOps
st.markdown("""
<div class="data-panel">
    <div class="data-panel-header">
        <div class="panel-title" style="margin:0; border:none; padding:0;">// Recent UserOperations</div>
    </div>
""", unsafe_allow_html=True)
display_df = df[['userophash', 'bundler_name', 'sender', 'blocknumber', 'time']].head(20).copy()
display_df.columns = ['UserOp Hash', 'Bundler', 'Sender', 'Block', 'Time']
st.dataframe(display_df, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# AI Analyst
st.markdown("""
<div class="ai-panel">
    <div class="panel-title">// AI Analyst</div>
    <div style="font-size:0.8rem; color:#444; margin-bottom:1rem; font-family:'Share Tech Mono',monospace; letter-spacing:0.05em;">
        Ask anything about the bundler data in plain English
    </div>
""", unsafe_allow_html=True)

user_question = st.text_input(
    "",
    placeholder="Which bundler should I use? Is the network healthy?",
    label_visibility="collapsed"
)

if user_question:
    with st.spinner("Analyzing..."):
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            summary = f"""You are an expert analyzing ERC-4337 Ethereum bundler data.
Answer in plain English a non-technical person can understand. Be concise and direct.

Current data:
- Total UserOps: {len(df):,}
- Unique Bundlers: {df['bundler'].nunique()}
- Unique Senders: {df['sender'].nunique():,}
- Top bundler: {top1_name} with {top1_share}% market share
- Top 3 bundlers combined: {top3_share:.1f}%

Top bundlers:
{bundler_stats[['bundler_name','total_userops','market_share']].head(10).to_string(index=False)}

Data range: {df['time'].min()} to {df['time'].max()}"""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=summary + "\n\nQuestion: " + user_question
            )
            st.markdown(f'<div class="ai-response">{response.text}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div class="footer">
    <div class="footer-left">
        Data sourced from Ethereum mainnet via Alchemy &nbsp;·&nbsp; Updates every 10 minutes &nbsp;·&nbsp; {len(df):,} UserOps collected
    </div>
    <div class="footer-right">
        <a href="https://github.com/Operant7-lang/erc4337-bundler-monitor">View Source</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)