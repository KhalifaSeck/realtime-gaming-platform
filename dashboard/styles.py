"""CSS injection + composants UI reutilisables."""
import streamlit as st


NEON_CYAN = "#00d9ff"
NEON_PINK = "#ff00d4"
NEON_PURPLE = "#7c3aed"
NEON_GREEN = "#00ff88"
NEON_ORANGE = "#ff8800"
BG_DARK = "#0d1117"
BG_CARD = "#161b22"
TEXT_LIGHT = "#e6edf3"

TIER_COLORS = {
    "superstar": "#ff00d4",
    "hit":       "#00d9ff",
    "mid":       "#7c3aed",
    "niche":     "#00ff88",
    "unknown":   "#6b7280",
}

SEVERITY_COLORS = {
    "High":   "#ff3860",
    "Medium": "#ffa500",
    "Low":    "#00d9ff",
}


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Rajdhani', sans-serif !important;
    }

    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1px;
        background: linear-gradient(135deg, #00d9ff 0%, #ff00d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero {
        background: radial-gradient(ellipse at top, rgba(0,217,255,0.15), transparent 70%);
        padding: 2rem 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(0,217,255,0.2);
    }

    .card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid rgba(0,217,255,0.15);
        border-radius: 10px;
        padding: 1rem;
        transition: all 0.3s ease;
    }

    .card:hover {
        border-color: #00d9ff;
        box-shadow: 0 0 20px rgba(0,217,255,0.3);
        transform: translateY(-2px);
    }

    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-right: 5px;
    }
    .badge-superstar { background: #ff00d4; color: white; }
    .badge-hit       { background: #00d9ff; color: black; }
    .badge-mid       { background: #7c3aed; color: white; }
    .badge-niche     { background: #00ff88; color: black; }
    .badge-unknown   { background: #6b7280; color: white; }
    .badge-high      { background: #ff3860; color: white; }
    .badge-medium    { background: #ffa500; color: black; }
    .badge-viral     { background: #ff00d4; color: white; animation: pulse 1.5s infinite; }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 5px #ff00d4; }
        50% { box-shadow: 0 0 20px #ff00d4, 0 0 30px #ff00d4; }
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid rgba(0,217,255,0.2);
        padding: 1rem;
        border-radius: 10px;
    }
    [data-testid="stMetricLabel"] {
        color: #00d9ff !important;
        text-transform: uppercase;
        font-weight: 700;
        font-size: 0.75rem !important;
        letter-spacing: 1px;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif !important;
        color: #e6edf3 !important;
        font-size: 2rem !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid rgba(0,217,255,0.2);
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.9rem;
        letter-spacing: 1px;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00d9ff !important;
        border-bottom: 3px solid #00d9ff !important;
    }

    /* DataFrame */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(0,217,255,0.15);
        border-radius: 8px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00d9ff 0%, #7c3aed 100%);
        color: white;
        border: none;
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
        border-radius: 6px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        box-shadow: 0 0 15px rgba(0,217,255,0.6);
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)


def tier_badge(tier: str) -> str:
    tier = (tier or "unknown").lower()
    return f'<span class="badge badge-{tier}">{tier}</span>'


def severity_badge(sev: str) -> str:
    return f'<span class="badge badge-{(sev or "").lower()}">{sev or "?"}</span>'


def viral_badge(label: str = "🔥 VIRAL") -> str:
    return f'<span class="badge badge-viral">{label}</span>'


def game_card(game: dict) -> str:
    """HTML card gaming pour un jeu."""
    name = game.get("GAME_NAME") or game.get("game_name") or "Unknown"
    appid = game.get("STEAM_APP_ID") or game.get("steam_app_id", "?")
    dev = game.get("DEVELOPER") or game.get("developer") or "-"
    pub = game.get("PUBLISHER") or game.get("publisher") or "-"
    genre = game.get("PRIMARY_GENRE") or game.get("PRIMARY_GENRE_FINAL") or game.get("primary_genre") or ""
    tier = game.get("POPULARITY_TIER") or game.get("popularity_tier") or "unknown"
    score = game.get("POPULARITY_SCORE") or game.get("popularity_score") or 0
    owners = game.get("OWNERS_ESTIMATE") or game.get("owners_estimate") or 0
    price = game.get("PRICE_USD") or game.get("price_usd") or 0

    return f"""
    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h4 style="margin:0; color:#e6edf3; font-family:'Orbitron', sans-serif;">{name}</h4>
        {tier_badge(tier)}
      </div>
      <div style="color:#8b949e; font-size:0.85rem; margin:6px 0;">
        AppID: <b>{appid}</b> · Genre: <b>{genre or '-'}</b>
      </div>
      <div style="color:#e6edf3; font-size:0.9rem;">
        🏢 {pub} · 🔨 {dev}
      </div>
      <div style="display:flex; gap:15px; margin-top:10px; font-size:0.85rem;">
        <span>🎯 <b style="color:#00d9ff;">{score:.1f}</b></span>
        <span>👥 <b>{owners:,}</b></span>
        <span>💵 <b>${price:.2f}</b></span>
      </div>
    </div>
    """