import json
import time
import streamlit as st
import plotly.graph_objects as go
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ClearClause | AI Threat Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN STYLING & ANIMATIONS CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1e1b4b 0%, #070a12 60%, #030408 100%);
        color: #f8fafc;
    }
    
    section[data-testid="stSidebar"] {
        background: #090d16 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 20%, #a855f7 70%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
        margin: 0;
    }
    
    .glass-card {
        background: rgba(17, 24, 39, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        height: 100%;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(168, 85, 247, 0.4);
    }
    
    .card-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 8px;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #3b82f6 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 14px 28px !important;
        box-shadow: 0 4px 25px rgba(236, 72, 153, 0.35) !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 8px 30px rgba(236, 72, 153, 0.65) !important;
    }

    /* Pulsing Badges */
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }
        50% { box-shadow: 0 0 25px rgba(239, 68, 68, 0.8); }
    }
    .glow-badge-high {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid #ef4444;
        color: #f87171;
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 800;
        animation: pulse-red 2s infinite;
    }
    .glow-badge-med {
        background: rgba(245, 158, 11, 0.2);
        border: 1px solid #f59e0b;
        color: #fbbf24;
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 800;
    }
    .glow-badge-low {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 800;
    }

    /* Loading Screen Glow Spinner */
    .loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        margin: 20px 0;
        background: rgba(17, 24, 39, 0.5);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 16px;
        backdrop-filter: blur(12px);
    }
    .spinner-ring {
        width: 60px;
        height: 60px;
        border: 5px solid rgba(255, 255, 255, 0.1);
        border-top: 5px solid #a855f7;
        border-right: 5px solid #ec4899;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        box-shadow: 0 0 25px rgba(168, 85, 247, 0.4);
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
""", unsafe_allow_html=True)

# --- DEMO SAMPLES ---
DEMO_SAMPLES = {
    "🚨 Shady VPN (Score ~10)": (
        "The user agrees that the Company may sell, license, and transfer all uploaded biometric data, "
        "voice recordings, precise GPS coordinates, and contact lists to third-party data brokers indefinitely. "
        "The Company assumes zero liability for data breaches or gross negligence. Any dispute must be handled "
        "through mandatory individual binding arbitration held exclusively in the Cayman Islands, and the user "
        "expressly waives all rights to participate in class-action lawsuits. A non-refundable inactivity fee of "
        "$29.99 will be automatically billed to your linked payment profile every 30 days without advance notification."
    ),
    "⚠️ Commercial Cloud Platform (Score ~55)": (
        "We log device hardware models, screen resolutions, and IP address histories to support personalization, "
        "system diagnostics, and programmatic promotional partners. These partners deploy persistent tracking cookies "
        "across our domains to develop broad interest profiles. Accounts that subscribe to recurring automated billing "
        "tiers renew automatically unless cancelled 48 hours prior to the close of the cycle. By submitting content, "
        "you grant the company a worldwide, perpetual, royalty-free, transferable license to host, parse, cache, index, "
        "and reformat user submissions for platform stability benchmarking. Any disputes shall be settled by binding arbitration."
    ),
    "🟢 Zero-Knowledge Messaging (Score ~98)": (
        "All communications and user files are end-to-end encrypted using client-side cryptographic keys that are "
        "never accessible to our servers or staff. We operate a strict zero-knowledge architecture: we do not collect, "
        "monitor, or store IP addresses, metadata, contact lists, or browsing telemetry. We do not sell, rent, or trade "
        "user data with external brokers. You retain 100% copyright ownership of all submitted media. Account deletion "
        "permanently and irreversibly purges all cryptographic identifiers from our clusters within 24 hours."
    )
}

def sync_preset():
    st.session_state["tos_input_field"] = DEMO_SAMPLES[st.session_state["demo_selector"]]

if "tos_input_field" not in st.session_state:
    st.session_state["tos_input_field"] = DEMO_SAMPLES["🚨 Shady VPN (Score ~10)"]

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("<h3 style='color: #a855f7;'>⚙️ Engine Config</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
    st.caption("🔒 Analyzed strictly in-memory.")
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #ec4899;'>🧪 Instant Benchmarks</h3>", unsafe_allow_html=True)
    st.selectbox("Select preset agreement:", list(DEMO_SAMPLES.keys()), key="demo_selector", on_change=sync_preset)

# --- PYDANTIC SCHEMA FOR GEMINI ---
class FlagItem(BaseModel):
    category: str = Field(description="One of: Data Selling, Hidden Fees, Legal Rights, Excessive Licensing, Surveillance")
    severity: str = Field(description="'High', 'Medium', or 'Low'")
    clause: str = Field(description="Exact problematic clause")
    plain_english: str = Field(description="Consumer harm explained clearly")

class RiskVector(BaseModel):
    data_privacy_risk: int = Field(description="Risk rating from 0 (Safe) to 100 (Predatory)")
    financial_trap_risk: int = Field(description="Risk rating from 0 (Safe) to 100 (Predatory)")
    legal_disenfranchisement: int = Field(description="Risk rating from 0 (Safe) to 100 (Predatory)")
    ip_usurpation_risk: int = Field(description="Risk rating from 0 (Safe) to 100 (Predatory)")
    tracking_surveillance_risk: int = Field(description="Risk rating from 0 (Safe) to 100 (Predatory)")

class ToSAnalysis(BaseModel):
    safety_score: int = Field(description="Safety score from 0 (predatory) to 100 (ethical)")
    verdict: str = Field(description="'High Risk', 'Moderate Risk', or 'Safe'")
    summary: str = Field(description="Punchy, actionable summary of the agreement")
    risk_vectors: RiskVector
    flags: list[FlagItem]

# --- HERO SECTION ---
st.markdown("""
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 12px;">
        <div style="background: linear-gradient(135deg, #ec4899, #8b5cf6); padding: 14px; border-radius: 16px; font-size: 2.2rem; line-height: 1; box-shadow: 0 0 25px rgba(139, 92, 246, 0.45);">
            🛡️
        </div>
        <div>
            <h1 class="hero-title">ClearClause AI</h1>
            <p style="color: #94a3b8; margin: 0; font-size: 1.05rem;">Automated Predatory Legalese & Dark-Pattern Exploit Engine</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Document Stats
active_text = st.session_state.get("tos_input_field", "")
word_count = len(active_text.split())
read_time = max(1, round(word_count / 220))

m_stat1, m_stat2, m_stat3 = st.columns(3)
m_stat1.caption(f"📝 Document Length: **{word_count} words**")
m_stat2.caption(f"⏱️ Estimated Read Time: **~{read_time} min**")
m_stat3.caption("⚡ Model: **Gemini 3.6**")

# Input field
tos_text = st.text_area(
    "Agreement Text to Inspect:",
    key="tos_input_field",
    height=160,
    placeholder="Paste agreement text here..."
)

analyze_btn = st.button("⚡ Scan & Expose Dark Patterns", type="primary", use_container_width=True)

# --- EXECUTION & ANIMATED SCANNING ---
if analyze_btn:
    if not api_key:
        st.error("Please provide a Gemini API Key in the left sidebar.")
    elif not tos_text.strip():
        st.warning("Please supply contract text before running the audit.")
    else:
        loader_placeholder = st.empty()
        
        stages = [
            ("Initializing neural analysis...", "Connecting to Gemini 3.6 reasoning engine"),
            ("Extracting contractual clauses...", "Stripping boilerplate and formatting trees"),
            ("Detecting arbitration & waiver traps...", "Auditing consumer litigation limitations"),
            ("Cross-referencing behavioral tracking...", "Profiling telemetry and tracking monetization"),
            ("Finalizing threat cockpit...", "Generating Plotly risk vector radar")
        ]

        loader_placeholder.markdown(f"""
            <div class="loader-container">
                <div class="spinner-ring"></div>
                <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin-top: 18px;">
                    {stages[0][0]}
                </div>
                <div style="color: #94a3b8; font-size: 0.88rem; margin-top: 4px;">
                    {stages[0][1]}
                </div>
            </div>
        """, unsafe_allow_html=True)

        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                "You are an adversarial legal privacy and consumer rights auditor. "
                "Expose all dark patterns, unilateral pricing amendments, arbitration traps, "
                "surveillance indexing, and user liabilities.\n\n"
                f"Document text:\n\"\"\"{tos_text}\"\"\""
            )

            # Cycle animation states during processing
            for main_text, sub_text in stages[1:3]:
                time.sleep(0.3)
                loader_placeholder.markdown(f"""
                    <div class="loader-container">
                        <div class="spinner-ring"></div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin-top: 18px;">
                            {main_text}
                        </div>
                        <div style="color: #94a3b8; font-size: 0.88rem; margin-top: 4px;">
                            {sub_text}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ToSAnalysis,
                    temperature=0.1
                )
            )

            for main_text, sub_text in stages[3:]:
                time.sleep(0.2)
                loader_placeholder.markdown(f"""
                    <div class="loader-container">
                        <div class="spinner-ring"></div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin-top: 18px;">
                            {main_text}
                        </div>
                        <div style="color: #94a3b8; font-size: 0.88rem; margin-top: 4px;">
                            {sub_text}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            loader_placeholder.empty()

            result = json.loads(response.text)
            score = max(0, min(100, result.get("safety_score", 50)))
            verdict = result.get("verdict", "Moderate Risk")
            flags = result.get("flags", [])
            vectors = result.get("risk_vectors", {})

            # Theme Routing
            if score <= 40:
                theme_color = "#ef4444"
                badge_class = "glow-badge-high"
                verdict_text = "CRITICAL RISK"
            elif score <= 75:
                theme_color = "#f59e0b"
                badge_class = "glow-badge-med"
                verdict_text = "MODERATE RISK"
            else:
                theme_color = "#10b981"
                badge_class = "glow-badge-low"
                verdict_text = "VERIFIED ETHICAL"

            circumference = 314.15
            stroke_dash = circumference - (score / 100.0) * circumference

            st.markdown("<br>", unsafe_allow_html=True)

            # --- TOP LEVEL DASHBOARD METRICS ---
            col1, col2, col3 = st.columns([1, 1.2, 1])

            with col1:
                st.markdown(f"""
                <div class="glass-card">
                    <div class="card-label">Safety Index</div>
                    <svg width="130" height="130" viewBox="0 0 120 120">
                        <circle cx="60" cy="60" r="50" fill="none" stroke="#1f2937" stroke-width="10" />
                        <circle cx="60" cy="60" r="50" fill="none" stroke="{theme_color}" stroke-width="10"
                                stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dash}"
                                stroke-linecap="round" transform="rotate(-90 60 60)" 
                                style="filter: drop-shadow(0 0 12px {theme_color}aa);" />
                        <text x="60" y="55" text-anchor="middle" dominant-baseline="central" 
                              fill="#ffffff" font-size="28" font-weight="800">{score}</text>
                        <text x="60" y="76" text-anchor="middle" dominant-baseline="central" 
                              fill="#94a3b8" font-size="11" font-weight="700">OUT OF 100</text>
                    </svg>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="glass-card">
                    <div class="card-label">Threat Classification</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: {theme_color}; margin: 8px 0 12px 0; text-shadow: 0 0 20px {theme_color}44;">
                        {verdict.upper()}
                    </div>
                    <span class="{badge_class}">
                        ● {verdict_text}
                    </span>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="glass-card">
                    <div class="card-label">Flagged Liabilities</div>
                    <div style="font-size: 3.4rem; font-weight: 800; color: #f8fafc; line-height: 1; margin: 8px 0;">
                        {len(flags)}
                    </div>
                    <span style="font-size: 0.85rem; color: #94a3b8;">High-Risk Vectors Exposed</span>
                </div>
                """, unsafe_allow_html=True)

            # --- SUMMARY CALLOUT ---
            st.markdown(f"""
            <div style="margin: 24px 0; background: rgba(139, 92, 246, 0.08); border-left: 5px solid #8b5cf6; padding: 18px 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.35);">
                <div style="color: #c084fc; font-weight: 800; font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px;">
                    ⚡ Threat Assessment Summary
                </div>
                <div style="color: #e2e8f0; font-size: 1.05rem; line-height: 1.6;">
                    {result.get('summary')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- BREAKDOWN & PLOTLY RADAR ---
            left_col, right_col = st.columns([1.1, 0.9])

            with left_col:
                st.markdown("### ⚠️ Extracted Red Flag Clauses")
                if not flags:
                    st.success("No predatory terms or high-risk clauses discovered.")
                else:
                    for item in flags:
                        sev = item.get("severity", "Medium")
                        border_col = "#ef4444" if sev == "High" else ("#f59e0b" if sev == "Medium" else "#10b981")
                        sev_badge = "glow-badge-high" if sev == "High" else ("glow-badge-med" if sev == "Medium" else "glow-badge-low")

                        st.markdown(f"""
                        <div style="background: rgba(17, 24, 39, 0.65); border: 1px solid rgba(255, 255, 255, 0.07); border-left: 5px solid {border_col}; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; backdrop-filter: blur(10px);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <strong style="color: #ffffff; font-size: 1.05rem;">{item.get('category')}</strong>
                                <span class="{sev_badge}">{sev.upper()} SEVERITY</span>
                            </div>
                            <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.5; margin: 0 0 10px 0;">{item.get('plain_english')}</p>
                            <div style="background: rgba(0, 0, 0, 0.45); border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; color: #94a3b8; font-style: italic; border: 1px solid rgba(255,255,255,0.05);">
                                "{item.get('clause')}"
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            with right_col:
                st.markdown("### 📡 Threat Vector Radar")
                
                # Interactive Radar Chart (Plotly)
                categories = ['Data Privacy','Financial Traps','Legal Rights','IP Seizure','Surveillance']
                values = [
                    vectors.get('data_privacy_risk', 50),
                    vectors.get('financial_trap_risk', 50),
                    vectors.get('legal_disenfranchisement', 50),
                    vectors.get('ip_usurpation_risk', 50),
                    vectors.get('tracking_surveillance_risk', 50)
                ]
            
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    fillcolor='rgba(236, 72, 153, 0.25)',
                    line=dict(color='#ec4899', width=2),
                    marker=dict(color='#a855f7', size=6)
                ))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True, 
                            range=[0, 100], 
                            tickfont=dict(color='#64748b', size=9), 
                            gridcolor='rgba(255,255,255,0.08)'
                        ),
                        angularaxis=dict(
                            tickfont=dict(color='#cbd5e1', size=11), 
                            gridcolor='rgba(255,255,255,0.08)'
                        )
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=40, r=40, t=30, b=30),
                    showlegend=False,
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)

                st.download_button(
                    label="💾 Export Audit Report (JSON)",
                    data=json.dumps(result, indent=2),
                    file_name="ClearClause_Threat_Audit.json",
                    mime="application/json",
                    use_container_width=True
                )

        except Exception as e:
            loader_placeholder.empty()
            st.error(f"Analysis failed: {str(e)}")