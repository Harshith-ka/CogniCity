"""
AI Digital Twin City — Analytics Dashboard (Phase 6)
Run with: streamlit run frontend/dashboard.py
"""

import json
import os
import time

import httpx

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
# API_BASE is the server-side URL Streamlit uses to reach the backend container
# (e.g. "http://backend:8000" inside Docker) — not reachable from the user's own
# browser, so any client-facing link (like the 3D view button) must use this instead.
PUBLIC_API_BASE = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000")

try:
    import streamlit as st
    import pandas as pd
    import plotly.graph_objects as go
    import streamlit.components.v1 as components
except ImportError:
    print("Install dependencies: pip install streamlit pandas plotly")
    raise

st.set_page_config(
    page_title="AI Twin City",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
# Custom CSS — COGNICITY_OS Cyber-Tactical Defense Aesthetic
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

    :root {
        --bg-deep: #06070a;
        --bg-surface: #0b0d13;
        --border-soft: #1c2230;
        --cyan-primary: #00e5ff;
        --cyan-glow: rgba(0, 229, 255, 0.45);
        --orange-primary: #ff6600;
        --orange-glow: rgba(255, 102, 0, 0.5);
        --text-primary: #edf2f7;
        --text-muted: #718096;
        --accent-indigo: #00e5ff;
        --accent-blue: #00e5ff;
        --accent-green: #00e676;
        --accent-amber: #ff6600;
        --accent-rose: #ff3366;
        --accent-violet: #00e5ff;
        --accent-teal: #00e5ff;
        --accent-gold: #ff6600;
    }

    html, body, [class*="css"], .stMarkdown, .stText, p, span, div, label {
        font-family: 'JetBrains Mono', monospace;
    }
    h1, h2, h3, h4, .hero-header h1 { font-family: 'Chakra Petch', sans-serif !important; letter-spacing: 0.5px; }

    .stApp {
        background-color: var(--bg-deep);
        background-image: 
            linear-gradient(rgba(0, 229, 255, 0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 229, 255, 0.025) 1px, transparent 1px);
        background-size: 32px 32px;
    }

    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }

    /* Hero header */
    .hero-header {
        background: #0b0d13;
        border: 1px solid #1c2230;
        border-left: 4px solid var(--cyan-primary);
        color: var(--text-primary);
        padding: 1rem 1.6rem;
        border-radius: 4px;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(0,0,0,0.6);
        position: relative;
    }
    .hero-header h1 { margin: 0; font-size: 1.6rem; font-weight: 800; color: #fff; letter-spacing: 1px; }
    .hero-header .subtitle { opacity: 0.7; font-size: 0.78rem; margin-top: 2px; color: var(--cyan-primary); font-weight: 700; }
    .hero-badge {
        background: var(--orange-primary);
        color: #000;
        padding: 4px 12px;
        border-radius: 2px;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 1px;
        box-shadow: 0 0 12px var(--orange-glow);
    }

    /* Tactical Status cards */
    .status-card {
        border-radius: 4px;
        padding: 0.85rem 1rem;
        text-align: center;
        margin-bottom: 0.5rem;
        background: #0f121a;
        border: 1px solid #1c2230;
        position: relative;
        transition: transform 0.12s ease;
    }
    .status-card::before {
        content: "";
        position: absolute; top: -1px; left: -1px;
        width: 6px; height: 6px;
        border-top: 2px solid var(--cyan-primary);
        border-left: 2px solid var(--cyan-primary);
    }
    .status-card::after {
        content: "";
        position: absolute; bottom: -1px; right: -1px;
        width: 6px; height: 6px;
        border-bottom: 2px solid var(--cyan-primary);
        border-right: 2px solid var(--cyan-primary);
    }
    .status-card:hover { transform: translateY(-2px); border-color: var(--cyan-primary); }
    .status-card .label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; color: var(--text-muted); }
    .status-card .value { font-size: 1.6rem; font-weight: 800; margin: 4px 0; font-family: 'Chakra Petch', sans-serif; color: #fff; }
    .status-card .delta { font-size: 0.7rem; color: var(--cyan-primary); font-weight: 700; }

    .card-blue   { border-color: rgba(0, 229, 255, 0.4); }
    .card-blue .value { color: var(--cyan-primary); }
    .card-green  { border-color: rgba(0, 230, 118, 0.4); }
    .card-green .value { color: #00e676; }
    .card-orange { border-color: rgba(255, 102, 0, 0.4); }
    .card-orange .value { color: var(--orange-primary); }
    .card-red    { border-color: rgba(255, 51, 102, 0.4); }
    .card-red .value { color: #ff3366; }
    .card-purple { border-color: rgba(0, 229, 255, 0.4); }
    .card-purple .value { color: var(--cyan-primary); }
    .card-teal   { border-color: rgba(0, 229, 255, 0.4); }
    .card-teal .value { color: var(--cyan-primary); }

    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 1.2rem 0 0.6rem 0;
        padding-bottom: 6px;
        border-bottom: 1px solid var(--border-soft);
    }
    .section-header .icon { font-size: 1.1rem; }
    .section-header h3 { margin: 0; font-size: 1rem; font-weight: 800; letter-spacing: 0.5px; color: var(--cyan-primary); font-family: 'Chakra Petch', sans-serif; }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #080a0e;
        border-right: 1px solid #1c2230;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 3px; border-bottom: 1px solid #1c2230; }
    .stTabs [data-baseweb="tab"] {
        padding: 6px 12px;
        font-size: 0.74rem;
        font-weight: 700;
        border-radius: 2px;
        color: #718096;
        background: #0b0d13;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #000 !important;
        background: var(--cyan-primary) !important;
        font-weight: 800 !important;
        box-shadow: 0 0 10px var(--cyan-glow);
    }

    /* Buttons */
    .stButton button {
        border-radius: 2px;
        border: 1px solid #2d3748;
        background: #0f121a;
        color: #fff;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.76rem;
    }
    .stButton button:hover { border-color: var(--cyan-primary); color: var(--cyan-primary); box-shadow: 0 0 10px var(--cyan-glow); }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════════════════════════════
def _auth_headers() -> dict:
    # The bearer token is this dashboard's own admin-portal session (see the login
    # gate below) — the same mechanism the mobile app uses, since Streamlit runs
    # server-side and can't rely on a browser's httpOnly cookie jar. Every request
    # this dashboard makes now carries it, so the backend's existing per-org feature
    # gates apply here too: an org restricted to a subset of modules sees exactly
    # that subset reflected in the tabs below, not a special dashboard-only rule.
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str):
    try:
        resp = httpx.get(f"{API_BASE}{path}", headers=_auth_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def api_post(path: str, data: dict | None = None):
    try:
        resp = httpx.post(f"{API_BASE}{path}", json=data or {}, headers=_auth_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════
# Auth gate — this dashboard now requires a real admin-portal login before
# rendering anything else. No fallback, no bypass: if there's no valid session,
# the rest of the script never runs (st.stop() below).
# ══════════════════════════════════════════════════════════════════════
def _render_login_screen():
    mode = st.session_state.get("dashboard_auth_mode", "login")
    st.markdown(
        '<div style="max-width:420px;margin:10vh auto 0;text-align:center;">'
        '<div style="font-size:2rem;">🏙️</div>'
        '<h2 style="margin:0.3rem 0;">AI Digital Twin City</h2>'
        f'<p style="color:#94a3b8;font-size:0.85rem;">'
        + ('Sign in with your platform account to open the dashboard.' if mode == "login"
           else 'Create a new organization — starts on the Free Trial plan.')
        + '</p></div>',
        unsafe_allow_html=True,
    )
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        if mode == "login":
            with st.form("dashboard_login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Enter both email and password.")
                else:
                    try:
                        resp = httpx.post(
                            f"{API_BASE}/api/auth/login",
                            json={"email": email, "password": password},
                            timeout=10,
                        )
                    except Exception:
                        st.error(f"Can't reach the backend at {API_BASE}.")
                    else:
                        if resp.status_code == 200:
                            user = resp.json()
                            st.session_state.auth_token = user.get("token")
                            st.session_state.current_user = user
                            st.rerun()
                        else:
                            st.error("Incorrect email or password.")

            st.markdown(
                '<p style="text-align:center;font-size:0.8rem;color:#64748b;margin-top:0.75rem;">'
                'New here? </p>',
                unsafe_allow_html=True,
            )
            if st.button("Create a new organization", use_container_width=True, key="show_signup_btn"):
                st.session_state.dashboard_auth_mode = "signup"
                st.rerun()
        else:
            with st.form("dashboard_signup_form"):
                org_name = st.text_input("Organization Name", placeholder="Acme Research Lab")
                name = st.text_input("Your Name", placeholder="Jane Doe")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password", help="Minimum 8 characters")
                submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if not org_name or not name or not email or len(password) < 8:
                    st.error("Fill in every field — password needs at least 8 characters.")
                else:
                    try:
                        resp = httpx.post(
                            f"{API_BASE}/api/auth/signup",
                            json={
                                "organization_name": org_name,
                                "name": name,
                                "email": email,
                                "password": password,
                            },
                            timeout=10,
                        )
                    except Exception:
                        st.error(f"Can't reach the backend at {API_BASE}.")
                    else:
                        if resp.status_code == 200:
                            user = resp.json()
                            st.session_state.auth_token = user.get("token")
                            st.session_state.current_user = user
                            st.rerun()
                        else:
                            detail = resp.json().get("detail", "Signup failed.") if resp.headers.get("content-type", "").startswith("application/json") else "Signup failed."
                            st.error(detail if isinstance(detail, str) else "Signup failed.")

            if st.button("Already have an account? Sign in", use_container_width=True, key="show_login_btn"):
                st.session_state.dashboard_auth_mode = "login"
                st.rerun()


if "current_user" not in st.session_state:
    _render_login_screen()
    st.stop()

# Fetch the signed-in user's own organization once per session — carries plan,
# agent_quota, allowed_environments, allowed_modules. None for a platform-level
# account (super_admin with no organization_id), which stays unrestricted.
if "current_org" not in st.session_state:
    _org_id = st.session_state.current_user.get("organization_id")
    st.session_state.current_org = api_get(f"/api/admin/organizations/{_org_id}") if _org_id else None


def _module_visible(module_key: str | None) -> bool:
    if module_key is None:
        return True  # core simulation surface — never gated by plan
    org = st.session_state.get("current_org")
    if not org:
        return True  # platform-level account or org fetch failed — unrestricted
    allowed = org.get("allowed_modules") or []
    return not allowed or module_key in allowed  # empty list == unrestricted


def _is_super_admin() -> bool:
    # This dashboard controls ONE shared city simulation, not a per-org one — plan
    # entitlements (_module_visible) decide which tabs an org can *view*, but
    # mutating the shared sim (start/stop, trigger disasters, run gov cycles) is a
    # platform-level action, not something every org's admin should be able to do.
    return st.session_state.current_user.get("role") == "super_admin"


def metric_card(label: str, value: str, color: str = "blue", delta: str = ""):
    delta_html = f'<div class="delta">{delta}</div>' if delta else ""
    st.markdown(
        f'<div class="status-card card-{color}">'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'{delta_html}</div>',
        unsafe_allow_html=True,
    )


def section_header(icon: str, title: str):
    st.markdown(
        f'<div class="section-header">'
        f'<span class="icon">{icon}</span>'
        f'<h3>{title}</h3></div>',
        unsafe_allow_html=True,
    )


def alert_card(text: str, level: str = "low"):
    st.markdown(
        f'<div class="alert-card alert-{level}">{text}</div>',
        unsafe_allow_html=True,
    )


def pct(v, fmt=".0%"):
    try:
        return f"{v:{fmt}}"
    except (TypeError, ValueError):
        return "—"


def dollar(v):
    try:
        return f"${v:,.0f}"
    except (TypeError, ValueError):
        return "—"


def citizen_avatar(gender: str, age: int) -> str:
    if age < 13:
        return "🧒"
    if age < 20:
        return "🧑‍🎓" if gender != "female" else "👧"
    bracket = "senior" if age >= 65 else "adult"
    table = {
        ("male", "adult"): "👨",
        ("female", "adult"): "👩",
        ("non_binary", "adult"): "🧑",
        ("male", "senior"): "👴",
        ("female", "senior"): "👵",
        ("non_binary", "senior"): "🧓",
    }
    return table.get((gender, bracket), "🧑")


def mood_emoji(happiness: float, stress: float) -> str:
    if happiness >= 0.75 and stress < 0.4:
        return "😄"
    if happiness >= 0.55:
        return "🙂"
    if stress >= 0.75:
        return "😰"
    if happiness < 0.3:
        return "😞"
    return "😐"


ACTIVITY_ICONS = {
    "idle": "💤", "sleep": "😴", "wake_up": "⏰", "work": "💼", "job_search": "🔍",
    "commute_to_work": "🚗", "commute_home": "🏠", "breakfast": "🥐", "lunch_break": "🥪",
    "dinner": "🍽", "eat_at_home": "🍽", "eat_at_restaurant": "🍽", "shopping": "🛍",
    "socialize": "🗣", "call_friend": "📞", "visit_neighbor": "🚪", "meeting": "🧑‍🤝‍🧑",
    "exercise": "🏃", "relax": "🛋", "watch_tv": "📺", "study": "📚", "learn_skill": "🎓",
    "read": "📖", "visit_hospital": "🏥", "invest": "📊", "freelance": "💻",
    "post_social_media": "📱", "worry_about_finances": "😟", "prepare_for_bed": "🛏",
}


def activity_icon(activity: str) -> str:
    return ACTIVITY_ICONS.get(activity, "▫️")


def personality_radar(traits: dict, name: str = "") -> go.Figure:
    axes = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    labels = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
    values = [round(traits.get(a, 0.5) * 100) for a in axes]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(124,108,246,0.25)",
        line=dict(color="#7c6cf6", width=2),
        name=name,
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=True, ticksuffix="%"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        margin=dict(l=30, r=30, t=20, b=20),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#c7c9d9"),
    )
    return fig


def happiness_color(h: float) -> str:
    h = max(0.0, min(1.0, h if h is not None else 0.5))
    stops = [(0.0, (240, 85, 111)), (0.5, (240, 168, 60)), (1.0, (45, 212, 167))]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= h <= t1:
            t = (h - t0) / (t1 - t0) if t1 > t0 else 0
            r = round(c0[0] + (c1[0] - c0[0]) * t)
            g = round(c0[1] + (c1[1] - c0[1]) * t)
            b = round(c0[2] + (c1[2] - c0[2]) * t)
            return f"#{r:02x}{g:02x}{b:02x}"
    return "#f0a83c"


def render_live_city_map(citizens: list, districts: list, conversations: list, height: int = 560) -> None:
    """Animated SVG map: citizen dots glide from their previous rendered position to
    their current one, and a dashed gold line links any two citizens currently talking
    face-to-face."""
    positioned = [c for c in citizens if c.get("x") is not None and c.get("y") is not None]
    if not positioned and not districts:
        st.info("No positioned citizens yet — step the simulation forward.")
        return

    xs = [d["center"][0] - d["radius"] for d in districts] + [d["center"][0] + d["radius"] for d in districts]
    ys = [d["center"][1] - d["radius"] for d in districts] + [d["center"][1] + d["radius"] for d in districts]
    if not xs:
        xs, ys = [-500, 500], [-500, 500]
    pad = 150
    min_x, max_x = min(xs) - pad, max(xs) + pad
    min_y, max_y = min(ys) - pad, max(ys) + pad
    vb_w, vb_h = max_x - min_x, max_y - min_y

    def sx(x):
        return x - min_x

    def sy(y):
        return max_y - y  # SVG y grows downward — flip so +y reads as "up"

    prev_pos = st.session_state.setdefault("live_map_prev_pos", {})

    tooltips = {}
    circle_svgs = []
    citizen_pos_by_id = {}
    for c in positioned:
        cid = str(c["id"])
        nx, ny = sx(c["x"]), sy(c["y"])
        citizen_pos_by_id[cid] = (nx, ny)
        px, py = prev_pos.get(cid, (nx, ny))
        color = happiness_color(c.get("happiness", 0.5))
        avatar = citizen_avatar(c.get("gender", ""), c.get("age", 30))
        mood = mood_emoji(c.get("happiness", 0), c.get("stress", 0))
        act = (c.get("current_activity") or "idle").replace("_", " ").title()
        tooltips[cid] = (
            f"{avatar} {c.get('name','')} {mood}<br>{c.get('occupation','')}<br>"
            f"{act}<br>📍 {c.get('district_name') or '—'}"
        )
        circle_svgs.append(
            f'<circle class="citizen-dot" data-id="{cid}" '
            f'cx="{px:.1f}" cy="{py:.1f}" data-x="{nx:.1f}" data-y="{ny:.1f}" '
            f'r="6" fill="{color}" stroke="rgba(10,11,16,0.85)" stroke-width="1.2" />'
        )
        prev_pos[cid] = (nx, ny)

    lines_svg = []
    seen_pairs = set()
    for conv in conversations or []:
        if conv.get("channel") != "face_to_face" or not conv.get("is_active", True):
            continue
        parts = [str(p) for p in (conv.get("participants") or [])]
        if len(parts) < 2:
            continue
        a, b = parts[0], parts[1]
        if a not in citizen_pos_by_id or b not in citizen_pos_by_id:
            continue
        pair_key = tuple(sorted([a, b]))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        x1, y1 = citizen_pos_by_id[a]
        x2, y2 = citizen_pos_by_id[b]
        lines_svg.append(
            f'<line class="interaction-line" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#e8b94d" stroke-width="1.6" stroke-dasharray="3,3" opacity="0" />'
        )

    district_svgs = []
    for d in districts:
        cx, cy = sx(d["center"][0]), sy(d["center"][1])
        r = d["radius"]
        district_svgs.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="rgba(124,108,246,0.05)" '
            f'stroke="rgba(124,108,246,0.4)" stroke-width="1.5" />'
            f'<text x="{cx:.1f}" y="{cy - r - 14:.1f}" text-anchor="middle" fill="#a89cf7" '
            f'font-size="13" font-family="Sora, sans-serif" font-weight="600">{d["name"]}</text>'
        )

    tooltip_json = json.dumps(tooltips)

    html_doc = f"""
    <div id="citymap-wrap" style="position:relative;width:100%;height:{height}px;
         background:radial-gradient(ellipse at 30% 0%, rgba(124,108,246,0.07), transparent 60%), #0d0e16;
         border-radius:16px;border:1px solid rgba(255,255,255,0.08);overflow:hidden;">
      <svg id="citymap-svg" viewBox="0 0 {vb_w:.0f} {vb_h:.0f}" style="width:100%;height:100%;display:block;">
        {''.join(district_svgs)}
        {''.join(lines_svg)}
        {''.join(circle_svgs)}
      </svg>
      <div id="citymap-tooltip" style="position:absolute;display:none;pointer-events:none;
           background:rgba(15,16,24,0.96);border:1px solid rgba(124,108,246,0.4);border-radius:10px;
           padding:8px 12px;font:500 12px 'Inter',sans-serif;color:#eceef5;line-height:1.5;
           box-shadow:0 8px 24px rgba(0,0,0,0.5);white-space:nowrap;z-index:10;"></div>
    </div>
    <style>
      .citizen-dot {{ transition: cx 1.3s cubic-bezier(0.4,0,0.2,1), cy 1.3s cubic-bezier(0.4,0,0.2,1); cursor: pointer; }}
      .interaction-line {{ transition: opacity 0.8s ease 0.3s; }}
    </style>
    <script>
      (function() {{
        const tooltips = {tooltip_json};
        const wrap = document.getElementById('citymap-wrap');
        const tip = document.getElementById('citymap-tooltip');
        document.querySelectorAll('.citizen-dot').forEach(function(el) {{
          el.addEventListener('mousemove', function(evt) {{
            const id = el.getAttribute('data-id');
            const rect = wrap.getBoundingClientRect();
            tip.innerHTML = tooltips[id] || '';
            tip.style.display = 'block';
            tip.style.left = (evt.clientX - rect.left + 14) + 'px';
            tip.style.top = (evt.clientY - rect.top + 10) + 'px';
          }});
          el.addEventListener('mouseleave', function() {{ tip.style.display = 'none'; }});
        }});
        requestAnimationFrame(function() {{
          requestAnimationFrame(function() {{
            document.querySelectorAll('.citizen-dot').forEach(function(el) {{
              el.setAttribute('cx', el.getAttribute('data-x'));
              el.setAttribute('cy', el.getAttribute('data-y'));
            }});
            document.querySelectorAll('.interaction-line').forEach(function(el) {{
              el.style.opacity = '1';
            }});
          }});
        }});
      }})();
    </script>
    """
    components.html(html_doc, height=height + 10, scrolling=False)


# ══════════════════════════════════════════════════════════════════════
# Twin Environment Marketplace — a modal, not a tab. The tab row is already
# overloaded; this gets its own dedicated surface reachable from anywhere.
# ══════════════════════════════════════════════════════════════════════
@st.dialog("🌐 Twin Environment Marketplace", width="large")
def show_marketplace_dialog():
    environments = api_get("/api/twin-platform/environments")
    if not environments:
        st.error("Couldn't reach the Twin Platform catalog. Is the backend up?")
        return

    selected_key = st.session_state.get("marketplace_selected_env")

    if not selected_key:
        st.caption("Browse the environment catalog. Pick one to configure and run it.")
        cols = st.columns(2)
        for i, env in enumerate(environments):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"##### {env['icon']} {env['name']}")
                    st.caption(f"{env['category']} • entities: {', '.join(env['entity_types'])}")
                    st.write(env["description"])
                    st.caption(f"Scenarios: {', '.join(env['scenario_examples'])}")
                    if st.button("Configure & Run →", key=f"mkt_pick_{env['key']}", use_container_width=True):
                        st.session_state["marketplace_selected_env"] = env["key"]
                        st.rerun()
        return

    env = next((e for e in environments if e["key"] == selected_key), None)
    if not env:
        st.session_state["marketplace_selected_env"] = None
        st.rerun()
        return

    if st.button("← Back to catalog"):
        st.session_state["marketplace_selected_env"] = None
        st.session_state.pop("marketplace_result", None)
        st.rerun()

    st.markdown(f"### {env['icon']} {env['name']}")
    st.caption(env["description"])

    is_city = env["key"] == "city"
    if is_city:
        st.warning(
            "This wraps the **live production city simulation** — a real tick can take "
            "over a minute with LLM-backed decisions. Runs here are capped at 1 tick."
        )

    c1, c2 = st.columns(2)
    with c1:
        ticks = st.number_input("Ticks to run", min_value=1, max_value=1 if is_city else 200, value=1 if is_city else 15)
        initial_agents = st.number_input("Extra agents to spawn (on top of defaults)", min_value=0, max_value=500, value=0)
    with c2:
        event_options = ["(none)"] + env["scenario_examples"]
        event_type = st.selectbox("Trigger a scenario mid-run", event_options)
        event_params_raw = st.text_input(
            "Scenario params (JSON, optional)",
            value="", placeholder='e.g. {"reduction_pct": 20} or {"count": 10}',
        )

    if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
        import json as _json
        try:
            event_params = _json.loads(event_params_raw) if event_params_raw.strip() else {}
        except ValueError:
            st.error("Scenario params must be valid JSON (or left blank).")
            event_params = None

        if event_params is not None:
            spinner_msg = (
                f"Running {env['name']}... a live city tick can take a minute or more"
                if is_city else f"Running {env['name']}..."
            )
            with st.spinner(spinner_msg):
                payload = {
                    "ticks": int(ticks),
                    "initial_agents": int(initial_agents),
                    "event_type": None if event_type == "(none)" else event_type,
                    "event_params": event_params,
                }
                try:
                    resp = httpx.post(
                        f"{API_BASE}/api/twin-platform/environments/{env['key']}/run",
                        json=payload,
                        timeout=180 if is_city else 30,
                    )
                    resp.raise_for_status()
                    st.session_state["marketplace_result"] = resp.json()
                except Exception as err:
                    st.error(f"Run failed: {err}")
                    st.session_state.pop("marketplace_result", None)

    result = st.session_state.get("marketplace_result")
    if result:
        st.markdown("---")
        st.markdown(f"##### Result — ran {result.get('ticks_run')} tick(s)")
        if result.get("capped"):
            st.caption(f"(capped from the requested {result.get('ticks_requested')} ticks)")
        if result.get("triggered_event"):
            st.info(f"Scenario triggered: {result['triggered_event']}")

        metrics = result.get("final_metrics") or {}
        if metrics:
            mcols = st.columns(3)
            for i, (k, v) in enumerate(metrics.items()):
                with mcols[i % 3]:
                    metric_card(k.replace("_", " ").title(), f"{v}", "teal")
        else:
            st.caption("No metrics returned.")


with st.sidebar:
    _user = st.session_state.current_user
    _org_label = _user.get("organization_name") or "Platform-level account"
    st.markdown(
        f'<div style="text-align:center;padding:0.3rem 0 0.5rem;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:0.5rem;">'
        f'<div style="font-weight:700;">{_user.get("name", _user.get("email"))}</div>'
        f'<div style="font-size:0.75rem;color:#94a3b8;">{_user.get("role", "").replace("_", " ")} · {_org_label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("Sign Out", use_container_width=True):
        try:
            httpx.post(f"{API_BASE}/api/auth/logout", headers=_auth_headers(), timeout=5)
        except Exception:
            pass
        st.session_state.pop("auth_token", None)
        st.session_state.pop("current_user", None)
        st.rerun()

    status = api_get("/api/simulation/status")
    sim_status = status.get("status", "stopped") if status else "offline"
    dot_class = {"running": "dot-running", "paused": "dot-paused"}.get(sim_status, "dot-stopped")

    st.markdown(
        f'<div style="text-align:center;padding:0.5rem 0">'
        f'<span class="status-dot {dot_class}"></span>'
        f'<b style="font-size:1.1rem">{sim_status.upper()}</b></div>',
        unsafe_allow_html=True,
    )

    if status:
        sc1, sc2 = st.columns(2)
        sc1.metric("Tick", status.get("current_tick", 0))
        sc2.metric("Pop", status.get("population", 0))
        sim_time = status.get("sim_time")
        if sim_time:
            st.caption(f"Sim: {str(sim_time)[:19]}")

    sidebar_weather = api_get("/api/weather/current")
    if sidebar_weather:
        w_icons = {"clear": "☀️", "cloudy": "☁️", "rain": "🌧", "storm": "⛈",
                   "snow": "❄️", "fog": "🌫", "heatwave": "🔥", "cold_snap": "🥶"}
        w_icon = w_icons.get(sidebar_weather["condition"], "🌤")
        st.caption(f"{w_icon} {sidebar_weather['condition'].replace('_',' ').title()} • {sidebar_weather['temperature_c']}°C • {sidebar_weather['season'].title()}")

    st.markdown(
        f'<a href="{PUBLIC_API_BASE}/city3d" target="_blank" style="display:block;text-align:center;'
        f'background:linear-gradient(135deg, rgba(124,108,246,0.25), rgba(232,185,77,0.18));'
        f'border:1px solid rgba(124,108,246,0.4);border-radius:10px;padding:9px 12px;'
        f'margin:0.6rem 0;color:#eceef5;text-decoration:none;font-weight:600;font-size:0.85rem;">'
        f'🏙️ Open 3D City View ↗</a>',
        unsafe_allow_html=True,
    )

    # Admin portal is the browser-facing /admin page (login, org/user management,
    # entitlements, usage) — same PUBLIC_API_BASE reasoning as the 3D view link
    # above: this opens in the signed-in user's own browser, not the Streamlit
    # server, so it must use the client-reachable host, not the server-side API_BASE.
    st.markdown(
        f'<a href="{PUBLIC_API_BASE}/admin" target="_blank" style="display:block;text-align:center;'
        f'background:linear-gradient(135deg, rgba(99,102,241,0.22), rgba(16,185,129,0.18));'
        f'border:1px solid rgba(99,102,241,0.4);border-radius:10px;padding:9px 12px;'
        f'margin:0.4rem 0 0.6rem;color:#eceef5;text-decoration:none;font-weight:600;font-size:0.85rem;">'
        f'🔐 Open Admin Panel ↗</a>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="background:linear-gradient(135deg, rgba(99,102,241,0.22), rgba(16,185,129,0.18));'
        f'border:1px solid rgba(99,102,241,0.45);border-radius:10px;padding:9px 12px;'
        f'margin:0.4rem 0;text-align:center;">'
        f'<div style="font-weight:700;font-size:0.84rem;color:#eceef5;">🧪 AI Agent Testing Sandbox</div>'
        f'<div style="font-size:0.72rem;color:#a5b4fc;margin-top:2px;">Click Tab #2 (AI Sandbox) at top ↗</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if _module_visible("twin_platform"):
        if st.button("🌐 Twin Environment Marketplace", use_container_width=True):
            show_marketplace_dialog()

    if _is_super_admin():
        st.markdown("---")
        st.markdown("##### Controls")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("▶", help="Start simulation"):
                api_post("/api/simulation/control", {"action": "start"})
                st.rerun()
        with c2:
            if st.button("⏸", help="Pause simulation"):
                api_post("/api/simulation/control", {"action": "pause"})
                st.rerun()
        with c3:
            if st.button("⏹", help="Stop simulation"):
                api_post("/api/simulation/control", {"action": "stop"})
                st.rerun()
        with c4:
            if st.button("⏭", help="Step x10"):
                api_post("/api/simulation/control", {"action": "step", "steps": 10})
                st.rerun()

        st.markdown("---")
        st.markdown("##### Trigger Events")

        sidebar_districts = api_get("/api/city/districts") or []
        location_options = ["🌆 Random / whole city"] + [f"📍 {d['name']}" for d in sidebar_districts]
        district_by_label = {f"📍 {d['name']}": d for d in sidebar_districts}

        def _gov_toast(r: dict) -> None:
            decisions = r.get("government_response") or []
            if decisions:
                depts = ", ".join(sorted({d["department"].title() for d in decisions}))
                st.toast(f"🏛 Government responded: {depts}", icon="🏛")

        with st.expander("🌪 City Event", expanded=False):
            templates = api_get("/api/events/templates")
            if templates:
                event_names = [t["name"] for t in templates]
                selected = st.selectbox("Event", event_names, label_visibility="collapsed")
                event_loc = st.selectbox("Location", location_options, key="event_loc")
                if st.button("Trigger", key="trig_event", use_container_width=True):
                    d = district_by_label.get(event_loc)
                    payload = {"event_name": selected}
                    if d:
                        payload.update({"area_x": d["center_x"], "area_y": d["center_y"], "radius": d["radius"] * 0.8})
                    r = api_post("/api/events/trigger", payload)
                    if r:
                        st.toast(f"Event: {r.get('name')} @ {event_loc}", icon="🌪")
                        _gov_toast(r)
                        st.rerun()

        with st.expander("💥 Disaster", expanded=False):
            disaster_type = st.selectbox(
                "Type", ["earthquake", "flood", "cyclone", "fire", "tornado", "tsunami", "landslide"],
                label_visibility="collapsed",
            )
            disaster_intensity = st.slider("Intensity", 0.1, 1.0, 0.7, 0.1, label_visibility="collapsed")
            disaster_loc = st.selectbox("Location", location_options, key="disaster_loc")
            if st.button("Trigger", key="trig_disaster", use_container_width=True):
                d = district_by_label.get(disaster_loc)
                payload = {"disaster_type": disaster_type, "intensity": disaster_intensity}
                if d:
                    payload.update({"epicenter_x": d["center_x"], "epicenter_y": d["center_y"]})
                r = api_post("/api/disasters/trigger", payload)
                if r:
                    st.toast(f"Disaster: {r.get('name')}", icon="💥")
                    _gov_toast(r)
                    st.rerun()

        with st.expander("🦠 Pandemic", expanded=False):
            if st.button("Start Pandemic", key="trig_pandemic", use_container_width=True):
                r = api_post("/api/pandemic/start", {"name": "Novel Virus Outbreak", "pathogen": "NV-1", "r0": 2.5, "initial_infected": 5})
                if r:
                    st.toast(f"Pandemic: {r.get('name')}", icon="🦠")
                    _gov_toast(r)
                    st.rerun()

        with st.expander("🗳 Election", expanded=False):
            if st.button("Start Election", key="trig_election", use_container_width=True):
                r = api_post("/api/elections/start", {"name": "City Mayor Election", "candidate_count": 4})
                if r:
                    st.toast(f"Election: {r.get('name')}", icon="🗳")
                    st.rerun()

        with st.expander("🏗 Infrastructure", expanded=False):
            infra_type_labels = {
                "hospital_build": "🏥 New Hospital",
                "school_build": "🏫 New School",
                "colony_build": "🏘 New Colony (housing)",
                "road_build": "🛣 New Road",
                "bridge_build": "🌉 New Bridge",
                "grid_upgrade": "⚡ Grid Modernization",
                "pipe_replacement": "🚰 Water Pipe Replacement",
                "fiber_install": "📡 Fiber Optic Install",
                "road_repair": "🔧 Road Resurfacing",
            }
            infra_type = st.selectbox(
                "Project", list(infra_type_labels.keys()),
                format_func=lambda t: infra_type_labels[t], label_visibility="collapsed", key="infra_type",
            )
            infra_loc = st.selectbox("Location", location_options, key="infra_loc")
            infra_target = None
            if infra_type == "road_build":
                target_options = [f"📍 {d['name']}" for d in sidebar_districts]
                if target_options:
                    infra_target_label = st.selectbox("Connects to", target_options, key="infra_target")
                    infra_target = district_by_label.get(infra_target_label)
            if st.button("Trigger", key="trig_infra", use_container_width=True):
                d = district_by_label.get(infra_loc)
                payload = {"project_type": infra_type}
                if d:
                    payload["district_id"] = d["id"]
                if infra_type == "road_build" and infra_target:
                    payload["target_x"] = infra_target["center_x"]
                    payload["target_y"] = infra_target["center_y"]
                r = api_post("/api/infrastructure/trigger", payload)
                if r:
                    st.toast(f"Project started: {r.get('name')}", icon="🏗")
                    st.rerun()

        with st.expander("🏛 Government", expanded=False):
            if st.button("Run Gov Cycle", key="gov_cycle", use_container_width=True):
                r = api_post("/api/government/run-cycle")
                if r:
                    st.toast(f"{r.get('count', 0)} decisions made", icon="🏛")
                    st.rerun()
            if st.button("Seed Relationships", key="seed_rel", use_container_width=True):
                r = api_post("/api/relationships/seed")
                if r:
                    st.toast(f"{r.get('relationships_created', 0)} created", icon="🤝")
    else:
        st.caption("🔒 Simulation controls and event triggers are platform-admin only. You have read access to this organization's data and metrics.")

    st.markdown("---")
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)

# ══════════════════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="hero-header">'
    '<div><h1>AI Digital Twin City</h1>'
    '<div class="subtitle">Multi-Agent Autonomous Smart City Simulation</div></div>'
    '<span class="hero-badge">PHASE 6 • v6.0</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════
# Tabs — filtered against the signed-in org's allowed_modules (see
# _module_visible() near the login gate). Empty/no org = unrestricted, same
# convention as everywhere else this is enforced. A tab absent here is a tab
# nobody can even click into, not just a locked one with a message inside it.
# ══════════════════════════════════════════════════════════════════════
_TAB_DEFS = [
    ("overview", "📊 Overview", None),
    ("sandbox", "🧪 AI Sandbox", "agent_eval"),
    ("live", "🎬 Live Feed", None),
    ("citizens", "👥 Citizens", None),
    ("econ", "💰 Economy", None),
    ("traffic", "🚗 Traffic", "traffic"),
    ("comms", "💬 Comms", "communication"),
    ("gov", "🏛 Gov", "government"),
    ("social", "🤝 Social", "relationships"),
    ("map", "🗺️ Map", None),
    ("events", "⚡ Events", None),
    ("disasters", "🌋 Disasters", "disasters"),
    ("pandemic", "🦠 Pandemic", "pandemic"),
    ("elections", "🗳 Elections", "elections"),
    ("social_media", "📱 Media", "social_media"),
    ("advisor", "🤖 AI Advisor", "ai_advisor"),
    ("graph", "🔗 Graph", "graph"),
    ("weather", "🌤 Weather", "weather"),
    ("crime", "🚔 Crime", "crime"),
    ("health", "🏥 Health", "healthcare"),
    ("edu", "🎓 Education", "education"),
    ("housing", "🏠 Housing", "housing"),
    ("news", "📰 News", "news"),
    ("culture", "🎭 Culture", "culture"),
    ("environment", "🌳 Environment", "environment"),
    ("demographics", "🧑‍🤝‍🧑 Demographics", "demographics"),
    ("infra", "⚡ Infrastructure", "infrastructure"),
    ("tourism", "✈️ Tourism", "tourism"),
]
_visible_tab_defs = [(k, label) for k, label, module in _TAB_DEFS if _module_visible(module)]
_tab_objs = st.tabs([label for _, label in _visible_tab_defs])
tabs = {key: obj for (key, _), obj in zip(_visible_tab_defs, _tab_objs)}

# ═══════════════════════════════════════
# TAB: Overview
# ═══════════════════════════════════════
if "overview" in tabs:
    with tabs["overview"]:
        metrics = api_get("/api/analytics/metrics")
        if metrics:
            section_header("📈", "City Vital Signs")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1:
                metric_card("Population", str(metrics.get("population", 0)), "blue")
            with c2:
                metric_card("Happiness", pct(metrics.get("avg_happiness", 0)), "green")
            with c3:
                metric_card("Health", pct(metrics.get("avg_health", 0)), "teal")
            with c4:
                metric_card("Stress", pct(metrics.get("avg_stress", 0)), "red")
            with c5:
                metric_card("GDP", dollar(metrics.get("total_gdp", 0)), "purple")
            with c6:
                metric_card("Unemployment", pct(metrics.get("unemployment_rate", 0)), "orange")

            st.write("")
            ec1, ec2, ec3, ec4 = st.columns(4)
            with ec1:
                metric_card("Employed", str(metrics.get("employed", 0)), "green")
            with ec2:
                metric_card("Unemployed", str(metrics.get("unemployed", 0)), "orange")
            with ec3:
                metric_card("Avg Income", dollar(metrics.get("avg_income", 0)), "purple")
            with ec4:
                metric_card("Active Events", str(metrics.get("active_events", 0)), "red")

        _org = st.session_state.get("current_org")
        if _org:
            section_header("🏛", f"Organization Usage — {_org['name']}")
            usage = api_get(f"/api/admin/organizations/{_org['id']}/usage")
            billing = api_get(f"/api/admin/organizations/{_org['id']}/billing")
            uc1, uc2, uc3, uc4, uc5 = st.columns(5)
            with uc1:
                plan_name = billing["plan"]["name"] if billing and billing.get("plan") else _org.get("plan_key", "—").title()
                metric_card("Plan", plan_name, "blue")
            with uc2:
                metric_card("Agent Quota", f"{_org.get('agent_quota', 0):,}", "purple")
            with uc3:
                # Real credits (Phase 3) — a super_admin grants these manually via
                # the admin portal; there's still no payment gateway behind it.
                bal = f"{billing['credits_balance']:,.0f}" if billing else "—"
                metric_card("Credits Balance", bal, "orange")
            if usage:
                ticks = usage["usage"]["agent_ticks"]
                reqs = usage["usage"]["api_request"]
                with uc4:
                    # "Agent-ticks", not "agent-hours" — a Twin Platform run is a
                    # synchronous burst of simulation ticks, not real wall-clock
                    # time, and labeling it hours would overstate the precision.
                    metric_card("Agent-Ticks Consumed", f"{ticks['total_quantity']:,.0f}", "teal")
                with uc5:
                    metric_card("Simulations Run", str(reqs["record_count"]), "green")
                st.caption(f"{ticks['record_count']} metered run{'s' if ticks['record_count'] != 1 else ''}.")
            else:
                with uc4:
                    metric_card("Agent-Ticks Consumed", "—", "teal")
                with uc5:
                    metric_card("Simulations Run", "—", "green")
                st.caption("Couldn't reach usage data.")

        history = api_get("/api/analytics/history?limit=100")
        if history and len(history) > 2:
            section_header("📉", "Historical Trends")
            df = pd.DataFrame(history)
            if "tick" in df.columns:
                df = df.set_index("tick")
                t1, t2 = st.columns(2)
                with t1:
                    st.caption("HAPPINESS • HEALTH • STRESS")
                    cols = [c for c in ["avg_happiness", "avg_health", "avg_stress"] if c in df.columns]
                    if cols:
                        st.area_chart(df[cols], height=220)
                with t2:
                    st.caption("GDP OVER TIME")
                    if "total_gdp" in df.columns:
                        st.area_chart(df[["total_gdp"]], height=220)

                t3, t4 = st.columns(2)
                with t3:
                    st.caption("UNEMPLOYMENT RATE")
                    if "unemployment_rate" in df.columns:
                        st.line_chart(df[["unemployment_rate"]], height=180)
                with t4:
                    st.caption("AVG CONGESTION")
                    if "avg_congestion" in df.columns:
                        st.line_chart(df[["avg_congestion"]], height=180)

        ticks = api_get("/api/simulation/ticks?count=50")
        if ticks and len(ticks) > 1:
            section_header("⚡", "Tick Performance (ms)")
            tick_df = pd.DataFrame(ticks)
            if "tick" in tick_df.columns and "duration_ms" in tick_df.columns:
                st.line_chart(tick_df.set_index("tick")["duration_ms"], height=150)

        population = api_get("/api/analytics/population")
        if population:
            section_header("🧑‍🤝‍🧑", "Demographics")
            d1, d2 = st.columns(2)
            with d1:
                st.caption("AGE DISTRIBUTION")
                age = population.get("by_age", {})
                if age:
                    st.bar_chart(age, height=200)
            with d2:
                st.caption("EDUCATION LEVELS")
                edu = population.get("by_education", {})
                if edu:
                    st.bar_chart(edu, height=200)

# ═══════════════════════════════════════
# TAB: AI Agent Testing Sandbox
# ═══════════════════════════════════════
if "sandbox" in tabs:
    with tabs["sandbox"]:
        section_header("🧪", "Universal AI Agent Testing Sandbox")
        st.caption("Safely evaluate candidate AI/ML models against isolated in-memory synthetic human cohorts before real-world deployment.")

        c_config, c_pop = st.columns([1.1, 0.9])

        with c_config:
            st.markdown("##### 🔌 1. Model & Target Feature Schema")
            agent_name = st.text_input("Agent / Model Name", value="CardioRisk-Predictor v3.2")
        
            domain_preset = st.selectbox(
                "Target Domain / Feature Schema",
                ["cardiology_uci", "credit_lending", "real_estate_housing", "ecommerce_recsys"],
                format_func=lambda x: {
                    "cardiology_uci": "❤️ Cardiology Biomarkers (UCI 13-Feature Schema: trestbps, chol, thalach, oldpeak...)",
                    "credit_lending": "💳 Credit & Underwriting (DTI, Credit Score, Savings, Loan Amount...)",
                    "real_estate_housing": "🏠 Housing & Real Estate (Budget, Downpayment, Preferred Sqft...)",
                    "ecommerce_recsys": "🛒 E-Commerce & Consumer Behavior (Income, Lifestyle, Price Sensitivity...)",
                }[x],
            )

            protocol = st.selectbox(
                "Connection Protocol",
                ["mock_benchmark", "uploaded_model", "rest_webhook", "openai_chat"],
                format_func=lambda x: {
                    "mock_benchmark": "⚡ Built-in Correlated Benchmark Simulator (Demo)",
                    "uploaded_model": "📁 Upload Your Own Model (.onnx)",
                    "rest_webhook": "🌐 REST API Webhook (POST /predict)",
                    "openai_chat": "🤖 OpenAI / LLM Chat Completion Endpoint",
                }[x],
            )

            endpoint_url = None
            api_key = None
            prompt_tmpl = None
            uploaded_model_id = st.session_state.get("sandbox_model_id")

            if protocol == "uploaded_model":
                st.caption(
                    "ONNX only, not pickle/joblib — loading an arbitrary `.pkl` file can execute "
                    "code embedded in it. ONNX is a static computation graph; running it can't. "
                    "Your model must accept a single float32 tensor of shape `[1, 8]`, in this exact "
                    "order: `age, annual_income, savings, monthly_expenses, credit_score_estimate, "
                    "health_index, stress_level, happiness`."
                )
                model_file = st.file_uploader("Model File", type=["onnx"], key="sandbox_model_uploader")
                if model_file is not None and st.session_state.get("sandbox_model_filename") != model_file.name:
                    with st.spinner(f"Validating {model_file.name}…"):
                        try:
                            resp = httpx.post(
                                f"{API_BASE}/api/eval/upload-model",
                                files={"file": (model_file.name, model_file.getvalue(), "application/octet-stream")},
                                headers=_auth_headers(),
                                timeout=30,
                            )
                            resp.raise_for_status()
                            meta = resp.json()
                            st.session_state["sandbox_model_id"] = meta["model_id"]
                            st.session_state["sandbox_model_filename"] = model_file.name
                            st.session_state["sandbox_model_meta"] = meta
                            uploaded_model_id = meta["model_id"]
                        except Exception as err:
                            st.session_state.pop("sandbox_model_id", None)
                            st.error(f"Model rejected: {err}")
                meta = st.session_state.get("sandbox_model_meta")
                if uploaded_model_id and meta:
                    st.success(
                        f"✓ {st.session_state.get('sandbox_model_filename')} loaded — "
                        f"input `{meta['input_name']}` shape `{meta['input_shape']}`, "
                        f"outputs `{', '.join(meta['output_names'])}`"
                    )
                elif not uploaded_model_id:
                    st.warning("Upload a model file before running the evaluation.")

            if protocol == "rest_webhook":
                endpoint_url = st.text_input("Webhook Endpoint URL", value="http://host.docker.internal:9000/predict")
                st.caption(
                    "⚠️ Testing a model running on **this same machine**? Use `host.docker.internal` "
                    "instead of `localhost` — the backend runs in a container, so `localhost` there means "
                    "the container itself, not your machine. Using `localhost` fails silently with a "
                    "network error on every citizen (and a misleadingly low robustness score)."
                )
                api_key = st.text_input("API Key / Bearer Token (Optional)", type="password")
            elif protocol == "openai_chat":
                endpoint_url = st.text_input("OpenAI-Compatible Base URL", value="https://api.openai.com/v1/chat/completions")
                st.caption(
                    "⚠️ Pointing this at a **locally-hosted** OpenAI-compatible server (Ollama, vLLM, "
                    "LM Studio, text-generation-webui, etc.) on this same machine? Use `host.docker.internal` "
                    "instead of `localhost` in the URL — e.g. `http://host.docker.internal:11434/v1/chat/completions`. "
                    "The backend runs in a container, so `localhost` there means the container itself, not "
                    "your machine, and every request will silently fail with a network error."
                )
                api_key = st.text_input("API Key", type="password")
                prompt_tmpl = st.text_area("Citizen Evaluation Prompt Template", value="Evaluate this correlated human profile and return risk assessment & recommendation: {profile}")

            c_mode, c_hor = st.columns(2)
            with c_mode:
                interaction_mode = st.selectbox(
                    "Interaction Mode",
                    ["one_shot", "longitudinal", "conversational"],
                    format_func=lambda x: {
                        "one_shot": "🎯 1-Shot Decision",
                        "longitudinal": "⏳ Multi-Month Drift",
                        "conversational": "💬 Synthetic Chat",
                    }[x],
                )
            with c_hor:
                horizon_days = st.selectbox("Simulation Horizon", [30, 90, 180, 365], index=1, format_func=lambda x: f"{x} Days")

        with c_pop:
            st.markdown("##### 👥 2. Correlated Population Generator")
            cohort = st.selectbox(
                "Demographic Population Cohort",
                [
                    "balanced_general",
                    "senior_population",
                    "low_income_high_debt",
                    "youth_tech_savvy",
                    "high_stress_chronic",
                    "adversarial_edge_cases",
                ],
                format_func=lambda x: {
                    "balanced_general": "🌆 Balanced General Metro Demographics",
                    "senior_population": "👵 Senior Citizens (Aged 60+, Chronic Healthcare)",
                    "low_income_high_debt": "💳 Low-Income & High-DTI Borrowers",
                    "youth_tech_savvy": "📱 Youth & Tech-Savvy Digital Natives",
                    "high_stress_chronic": "🩺 Elevated Stress & Chronic Condition Cohort",
                    "adversarial_edge_cases": "🔥 Adversarial Edge-Case Stress Cohort",
                }[x],
            )

            sample_size = st.slider("Synthetic Human Sample Size", min_value=50, max_value=5000, value=500, step=50)
            adversarial_intensity = st.slider("Adversarial Perturbation Intensity", min_value=0.0, max_value=1.0, value=0.25, step=0.05)

            st.info("🧠 **Causal Bayesian Generator**: All features are generated using multi-layer joint distributions preserving cross-variable physiology and financial correlations.")

        st.write("")
        run_blocked = protocol == "uploaded_model" and not uploaded_model_id
        if st.button(
            "🚀 Run Agent Behavioral Evaluation & Drift Simulation",
            use_container_width=True, type="primary", disabled=run_blocked,
        ):
            with st.spinner(f"Synthesizing {sample_size:,} correlated humans ({domain_preset}) and evaluating agent '{agent_name}'..."):
                req_payload = {
                    "agent_name": agent_name,
                    "domain_preset": domain_preset,
                    "protocol": protocol,
                    "endpoint_url": endpoint_url,
                    "api_key": api_key,
                    "model_id": uploaded_model_id if protocol == "uploaded_model" else None,
                    "interaction_mode": interaction_mode,
                    "prompt_template": prompt_tmpl,
                    "cohort_distribution": cohort,
                    "sample_size": sample_size,
                    "adversarial_intensity": adversarial_intensity,
                    "simulation_horizon_days": horizon_days,
                }
                scorecard = api_post("/api/eval/run-test", req_payload)

                if scorecard:
                    st.session_state["latest_scorecard"] = scorecard
                    st.success(f"Evaluation complete for '{agent_name}' across {sample_size:,} synthetic citizens!")

        # Display Scorecard if available
        latest = st.session_state.get("latest_scorecard")
        if latest:
            st.markdown("---")
            st.markdown(f"### 📋 Behavioral & Longitudinal Scorecard: **{latest.get('agent_name')}**")
            st.caption(f"Domain: `{latest.get('domain')}` • Test ID: `{latest.get('test_id')}` • Sample: {latest.get('population_size'):,} Correlated Synthetic Citizens")

            # Top KPI Metrics
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                metric_card("Adoption / Acceptance Rate", f"{latest.get('overall_adoption_rate', 0)}%", "green" if latest.get('overall_adoption_rate', 0) > 60 else "orange")
            with k2:
                metric_card("Synthetic Human Trust", f"{latest.get('avg_trust_index', 0)} / 1.0", "teal")
            with k3:
                metric_card("Robustness Score", f"{latest.get('robustness_score', 0)}%", "purple")
            with k4:
                metric_card("Fairness Parity Index", f"{latest.get('fairness_index', 0)} / 1.0", "blue" if latest.get('fairness_index', 0) > 0.8 else "red")

            # Summary box
            st.info(f"**Executive Synthesis**: {latest.get('executive_summary', '')}")

            # Longitudinal Trajectory Chart if available
            long_data = latest.get("longitudinal_summary")
            if long_data and long_data.get("timeline_snapshots"):
                st.markdown("##### ⏳ Longitudinal State Evolution & Intervention Efficacy")
                snapshots = long_data["timeline_snapshots"]
                df_timeline = pd.DataFrame([{
                    "Day": s["day"],
                    "Avg Blood Pressure (mmHg)": s["avg_systolic_bp"],
                    "Avg Cholesterol (mg/dl)": s["avg_cholesterol"],
                    "Active Compliance Rate (%)": s["active_compliance_rate"],
                    "High Risk Population (%)": s["high_risk_population_pct"],
                } for s in snapshots]).set_index("Day")

                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    st.caption("HEALTH BIOMARKER TRAJECTORY (Intervention vs Fatigue)")
                    st.line_chart(df_timeline[["Avg Blood Pressure (mmHg)", "Avg Cholesterol (mg/dl)"]], height=220)
                with c_t2:
                    st.caption("RISK REDUCTION & ADHERENCE DECAY OVER TIME")
                    st.line_chart(df_timeline[["High Risk Population (%)", "Active Compliance Rate (%)"]], height=220)

                st.caption(f"💡 **Behavioral Insight**: {long_data.get('behavioral_takeaway', '')}")

            # Demographic Fairness Breakdown
            dem_metrics = latest.get("demographic_fairness", [])
            if dem_metrics:
                st.markdown("##### ⚖️ Demographic Fairness & Parity Audit")
                df_dem = pd.DataFrame([{
                    "Demographic Cohort": m["demographic_group"],
                    "Sample Count": m["sample_count"],
                    "Adoption / Acceptance Rate": f"{m['acceptance_rate']}%",
                    "Trust Score": f"{m['avg_trust_score']} / 1.0",
                    "Disparity Ratio": f"{m['disparity_ratio']}x",
                    "Status": "✅ Fair" if m["status"] == "fair" else "⚠️ Disparity Detected",
                } for m in dem_metrics])
                st.dataframe(df_dem, use_container_width=True, hide_index=True)

            # Failure Mode Clusters
            clusters = latest.get("failure_clusters", [])
            if clusters:
                st.markdown("##### 🚨 Automated Adversarial Failure Mode Clusters")
                for c in clusters:
                    with st.expander(f"⚠️ {c['cluster_name']} ({c['affected_percentage']}% of failure cohort, N={c['sample_size']})", expanded=True):
                        st.markdown(f"**Root Cause**: {c['root_cause']}")
                        st.markdown(f"**Common Traits in Vulnerable Cohort**: `{'`, `'.join(c.get('common_traits', []))}`")
                        st.markdown(f"💡 **Recommended Calibration**: {c['suggested_fix']}")

            # Sample Citizen Interaction Logs
            samples = latest.get("sample_interactions", [])
            if samples:
                st.markdown("##### 📝 Representative Correlated Synthetic Interaction Logs")
                df_samples = pd.DataFrame([{
                    "Citizen ID": s["citizen_id"],
                    "Name": s["citizen_name"],
                    "Correlated Biomarkers": s["demographics_summary"],
                    "Model Output": str(s["agent_raw_output"].get("decision", s["agent_raw_output"].get("score", "Processed"))),
                    "Decision Accepted": "✅ Yes" if s["decision_accepted"] else "❌ No",
                    "Trust Delta": f"{'+' if s['trust_score_delta']>0 else ''}{s['trust_score_delta']}",
                    "Adversarial Failure": "🚨 Error/Bias" if s["is_adversarial_failure"] else "Normal",
                } for s in samples])
                st.dataframe(df_samples, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════
# TAB: Live Feed
# ═══════════════════════════════════════
if "live" in tabs:
    with tabs["live"]:
        live_citizens = api_get("/api/citizens/?limit=1200") or []
        citizen_by_id = {c["id"]: c for c in live_citizens}

        if live_citizens:
            section_header("🎬", "What's happening right now")
            activity_counts = {}
            for c in live_citizens:
                a = c.get("current_activity", "idle")
                activity_counts[a] = activity_counts.get(a, 0) + 1

            top_activities = sorted(activity_counts.items(), key=lambda kv: -kv[1])[:6]
            cols = st.columns(len(top_activities)) if top_activities else []
            for col, (act, count) in zip(cols, top_activities):
                with col:
                    metric_card(f"{activity_icon(act)} {act.replace('_',' ').title()}", str(count), "blue")

            st.write("")
            st.caption("LIVE CITIZEN ACTIVITY")
            grid_search = st.text_input("🔍 Filter by name, activity, or district", key="live_search")
            grid_citizens = live_citizens
            if grid_search:
                gs = grid_search.lower()
                grid_citizens = [
                    c for c in live_citizens
                    if gs in c.get("name", "").lower()
                    or gs in c.get("current_activity", "").lower()
                    or gs in (c.get("district_name") or "").lower()
                ]

            ncols = 4
            rows = [grid_citizens[i:i + ncols] for i in range(0, min(len(grid_citizens), 40), ncols)]
            for row in rows:
                row_cols = st.columns(ncols)
                for col, c in zip(row_cols, row):
                    with col:
                        avatar = citizen_avatar(c.get("gender", ""), c.get("age", 30))
                        mood = mood_emoji(c.get("happiness", 0), c.get("stress", 0))
                        act = c.get("current_activity", "idle")
                        st.markdown(
                            f'<div class="feed-card" style="text-align:center;padding:0.7rem 0.5rem;">'
                            f'<div style="font-size:1.8rem;">{avatar}</div>'
                            f'<div class="author" style="margin-top:2px;">{c.get("name","")} {mood}</div>'
                            f'<div class="meta">{activity_icon(act)} {act.replace("_"," ").title()}</div>'
                            f'<div class="meta">📍 {c.get("district_name") or "—"}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
            if len(grid_citizens) > 40:
                st.caption(f"Showing 40 of {len(grid_citizens)} citizens — use the filter to narrow down.")
        else:
            st.info("No citizens yet. Start the simulation.")

        st.markdown("---")
        section_header("💬", "Who's talking to whom")
        live_convos = api_get("/api/communication/conversations?limit=15")
        channel_icons = {"face_to_face": "🧑‍🤝‍🧑", "phone_call": "📞", "text_message": "💬",
                          "email": "📧", "social_media": "📱", "group_chat": "👥"}
        if live_convos:
            convo_cols = st.columns(2)
            for i, convo in enumerate(live_convos[:10]):
                parts = convo.get("participants") or []
                people = [citizen_by_id.get(str(p)) for p in parts]
                people = [p for p in people if p]
                with convo_cols[i % 2]:
                    if len(people) >= 2:
                        a, b = people[0], people[1]
                        a_av = citizen_avatar(a.get("gender", ""), a.get("age", 30))
                        b_av = citizen_avatar(b.get("gender", ""), b.get("age", 30))
                        who = f"{a_av} <strong>{a.get('name','')}</strong> {channel_icons.get(convo.get('channel',''), '💬')} {b_av} <strong>{b.get('name','')}</strong>"
                    elif len(people) == 1:
                        a = people[0]
                        who = f"{citizen_avatar(a.get('gender',''), a.get('age',30))} <strong>{a.get('name','')}</strong> {channel_icons.get(convo.get('channel',''), '💬')} someone"
                    else:
                        who = f"{channel_icons.get(convo.get('channel',''), '💬')} Two citizens"
                    status = "🟢 live" if convo.get("is_active") else "⚪ ended"
                    st.markdown(
                        f'<div class="feed-card"><div class="content">{who}</div>'
                        f'<div class="meta">"{convo.get("topic","")}" • {convo.get("channel","").replace("_"," ").title()} • {status}'
                        + (f' • 📍 {convo.get("location")}' if convo.get("location") else '') + '</div></div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("No conversations yet — they start once citizens are close enough to interact.")

        st.markdown("---")
        fc1, fc2 = st.columns(2)
        with fc1:
            section_header("📜", "Recent Life Events")
            events = api_get("/api/demographics/events?limit=12")
            if events:
                event_icons = {"birth": "👶", "death": "🕊", "marriage": "💍", "divorce": "💔",
                                "immigration": "🛬", "emigration": "🛫", "retirement": "🌅", "promotion": "📈"}
                for e in events:
                    icon = event_icons.get(e.get("type", ""), "📌")
                    st.markdown(
                        f'<div class="feed-card"><div class="content">{icon} {e.get("description","")}</div>'
                        f'<div class="meta">{str(e.get("timestamp",""))[:19]}</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No life events yet.")

        with fc2:
            section_header("💸", "Recent Transactions")
            txns = api_get("/api/economy/transactions?limit=12")
            if txns:
                for t in txns:
                    actor = citizen_by_id.get(t.get("citizen_id", ""))
                    actor_name = actor["name"] if actor else "Someone"
                    avatar = citizen_avatar(actor.get("gender", ""), actor.get("age", 30)) if actor else "🧑"
                    amt = t.get("amount", 0)
                    sign = "+" if amt >= 0 else "-"
                    st.markdown(
                        f'<div class="feed-card"><div class="content">{avatar} <strong>{actor_name}</strong> — '
                        f'{t.get("description") or t.get("type","").title()}</div>'
                        f'<div class="meta">{sign}{dollar(abs(amt))} • {t.get("type","").title()}</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No transactions yet.")

# ═══════════════════════════════════════
# TAB: Citizens
# ═══════════════════════════════════════
if "citizens" in tabs:
    with tabs["citizens"]:
        section_header("👥", "Citizen Directory")
        citizens = api_get("/api/citizens/?limit=1200")
        if citizens:
            search = st.text_input("🔍 Search by name or occupation", key="cit_search")
            if search:
                citizens = [
                    c for c in citizens
                    if search.lower() in c.get("name", "").lower()
                    or search.lower() in c.get("occupation", "").lower()
                ]

            cit_df = pd.DataFrame([{
                "": citizen_avatar(c.get("gender", ""), c.get("age", 30)),
                "Mood": mood_emoji(c.get("happiness", 0), c.get("stress", 0)),
                "Name": c.get("name", ""),
                "Age": c.get("age", 0),
                "Occupation": c.get("occupation", ""),
                "Happiness": round(c.get("happiness", 0), 2),
                "Health": round(c.get("health", 0), 2),
                "Stress": round(c.get("stress", 0), 2),
                "Balance": round(c.get("balance", 0), 0),
                "Activity": f"{activity_icon(c.get('current_activity',''))} {c.get('current_activity', '').replace('_',' ').title()}",
                "District": c.get("district_name") or "—",
            } for c in citizens])
            st.dataframe(
                cit_df,
                use_container_width=True,
                column_config={
                    "Happiness": st.column_config.ProgressColumn("Happiness", min_value=0, max_value=1, format="%.0f%%"),
                    "Health": st.column_config.ProgressColumn("Health", min_value=0, max_value=1, format="%.0f%%"),
                    "Stress": st.column_config.ProgressColumn("Stress", min_value=0, max_value=1, format="%.0f%%"),
                    "Balance": st.column_config.NumberColumn("Balance", format="$%.0f"),
                },
                height=380,
            )
            st.caption(f"Showing {len(citizens)} citizens")

        stats = api_get("/api/citizens/stats/summary")
        if stats:
            section_header("📊", "Population Stats")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                metric_card("Avg Age", f"{stats.get('avg_age', 0):.1f}", "blue")
            with s2:
                metric_card("Avg Balance", dollar(stats.get("avg_balance", 0)), "purple")
            with s3:
                metric_card("Avg Happiness", pct(stats.get("avg_happiness", 0)), "green")
            with s4:
                metric_card("Avg Stress", pct(stats.get("avg_stress", 0)), "red")

        st.markdown("---")
        section_header("🪪", "Citizen Profile")
        if citizens:
            profile_names = {f"{citizen_avatar(c.get('gender',''), c.get('age',30))} {c.get('name','')}": c["id"] for c in citizens}
            picked = st.selectbox("Select a citizen to inspect", list(profile_names.keys()), key="profile_pick")
            if picked:
                pid = profile_names[picked]
                detail = api_get(f"/api/citizens/{pid}")
                if detail:
                    avatar = citizen_avatar(detail.get("gender", ""), detail.get("age", 30))
                    mood = mood_emoji(detail.get("happiness", 0), detail.get("stress", 0))
                    st.markdown(
                        f'<div class="feed-card" style="display:flex;align-items:center;gap:16px;padding:1rem 1.2rem;">'
                        f'<div style="font-size:2.8rem;line-height:1;">{avatar}</div>'
                        f'<div>'
                        f'<div style="font-size:1.3rem;font-weight:700;">{detail.get("name","")} {mood}</div>'
                        f'<div style="opacity:0.7;font-size:0.9rem;">{detail.get("age",0)} yrs • {detail.get("occupation","")} • '
                        f'{activity_icon(detail.get("current_activity",""))} {detail.get("current_activity","").replace("_"," ").title()}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

                    p1, p2, p3, p4, p5, p6 = st.columns(6)
                    with p1:
                        metric_card("Happiness", pct(detail.get("happiness", 0)), "green")
                    with p2:
                        metric_card("Health", pct(detail.get("health", 0)), "teal")
                    with p3:
                        metric_card("Stress", pct(detail.get("stress", 0)), "red")
                    with p4:
                        metric_card("Energy", pct(detail.get("energy", 0)), "blue")
                    with p5:
                        metric_card("Balance", dollar(detail.get("balance", 0)), "purple")
                    with p6:
                        metric_card("Salary", dollar(detail.get("salary", 0)), "orange")

                    pc1, pc2 = st.columns([1, 1])
                    with pc1:
                        st.caption("PERSONALITY (BIG FIVE)")
                        traits = detail.get("personality_traits") or {}
                        if traits:
                            st.plotly_chart(personality_radar(traits, detail.get("name", "")), use_container_width=True, config={"displayModeBar": False})
                        else:
                            st.info("No personality data.")
                    with pc2:
                        st.caption("GOALS")
                        goals = detail.get("goals") or []
                        if goals:
                            for g in goals:
                                st.write(f"🎯 {g}")
                        else:
                            st.caption("No stated goals.")
                        st.caption("TRANSPORT & POLITICS")
                        st.write(f"🚗 Prefers: {detail.get('transport_preference','').title()}")
                        st.write(f"🗳 Political lean: {detail.get('political_opinion', 0.5):.2f} (0=liberal, 1=conservative)")

                    mc1, mc2 = st.columns(2)
                    with mc1:
                        st.caption("RECENT MEMORIES")
                        memories = api_get(f"/api/citizens/{pid}/memories?limit=8")
                        if memories:
                            for m in memories:
                                st.markdown(
                                    f'<div class="feed-card"><div class="content">{m.get("content","")}</div>'
                                    f'<div class="meta">🏷 {m.get("type","")} • importance {pct(m.get("importance",0))}</div></div>',
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.caption("No memories recorded yet.")
                    with mc2:
                        st.caption("RELATIONSHIPS")
                        graph = api_get(f"/api/relationships/citizens/{pid}/graph")
                        if graph and graph.get("edges"):
                            for edge in graph["edges"][:8]:
                                node = next((n for n in graph["nodes"] if n["id"] == edge["to"]), None)
                                label = node["label"] if node else edge["to"][:8]
                                st.write(f"🤝 **{label}** — `{edge['type']}` trust {pct(edge['trust'])}, closeness {pct(edge['closeness'])}")
                        else:
                            st.caption("No relationships yet.")

                    st.caption("RECENT TRANSACTIONS")
                    txns = api_get(f"/api/economy/transactions?citizen_id={pid}&limit=10")
                    if txns:
                        st.dataframe(pd.DataFrame([{
                            "Type": t.get("type", "").title(),
                            "Amount": round(t.get("amount", 0), 2),
                            "Description": t.get("description", ""),
                            "When": str(t.get("sim_timestamp", ""))[:19],
                        } for t in txns]), use_container_width=True, hide_index=True,
                            column_config={"Amount": st.column_config.NumberColumn("Amount", format="$%.2f")},
                        )
                    else:
                        st.caption("No transactions yet.")

# ═══════════════════════════════════════
# TAB: Economy
# ═══════════════════════════════════════
if "econ" in tabs:
    with tabs["econ"]:
        econ = api_get("/api/economy/stats")
        if econ:
            section_header("💰", "Economy Overview")
            e1, e2, e3, e4 = st.columns(4)
            with e1:
                metric_card("Total Wealth", dollar(econ.get("total_wealth", 0)), "purple")
            with e2:
                metric_card("Avg Salary", dollar(econ.get("avg_salary", 0)), "green")
            with e3:
                metric_card("Tax Rate", pct(econ.get("tax_rate", 0)), "orange")
            with e4:
                metric_card("Active Biz", str(econ.get("active_businesses", 0)), "blue")

        businesses = api_get("/api/economy/businesses")
        if businesses:
            section_header("🏢", f"Businesses ({len(businesses)})")
            biz_df = pd.DataFrame([{
                "Name": b.get("name", ""),
                "Type": b.get("type", ""),
                "Balance": round(b.get("balance", 0)),
                "Revenue": round(b.get("revenue", 0)),
                "Employees": b.get("max_employees", 0),
                "Status": "Open" if b.get("is_open") else "Closed",
            } for b in businesses])
            st.dataframe(
                biz_df, use_container_width=True,
                column_config={
                    "Balance": st.column_config.NumberColumn("Balance", format="$%.0f"),
                    "Revenue": st.column_config.NumberColumn("Revenue", format="$%.0f"),
                },
                height=350,
            )

        txns = api_get("/api/economy/transactions?limit=20")
        if txns:
            section_header("📋", "Recent Transactions")
            st.dataframe(
                pd.DataFrame([{
                    "Type": t.get("type", ""),
                    "Amount": round(t.get("amount", 0), 2),
                    "Description": t.get("description", ""),
                } for t in txns]),
                use_container_width=True,
                column_config={"Amount": st.column_config.NumberColumn("Amount", format="$%.2f")},
            )

# ═══════════════════════════════════════
# TAB: Traffic
# ═══════════════════════════════════════
if "traffic" in tabs:
    with tabs["traffic"]:
        traffic = api_get("/api/traffic/stats")
        if traffic:
            section_header("🚗", "Traffic Dashboard")
            t1, t2, t3, t4 = st.columns(4)
            with t1:
                metric_card("Recent Trips", str(traffic.get("total_recent_trips", 0)), "blue")
            with t2:
                metric_card("Avg Distance", f"{traffic.get('avg_distance_m', 0):,.0f}m", "teal")
            with t3:
                metric_card("Avg Duration", f"{traffic.get('avg_duration_min', 0):.1f}min", "green")
            with t4:
                metric_card("Rush Factor", f"{traffic.get('rush_hour_factor', 1.0):.1f}x", "orange")

            by_vehicle = traffic.get("trips_by_vehicle", {})
            if by_vehicle:
                section_header("🚙", "Trips by Vehicle Type")
                st.bar_chart(by_vehicle, height=200)

        congestion = api_get("/api/traffic/congestion")
        if congestion and len(congestion) > 0:
            section_header("🚦", f"Congested Segments ({len(congestion)})")
            st.dataframe(pd.DataFrame([{
                "From": f"({s['from'][0]:.0f}, {s['from'][1]:.0f})",
                "To": f"({s['to'][0]:.0f}, {s['to'][1]:.0f})",
                "Congestion": round(s["congestion"], 2),
                "Speed (km/h)": round(s["speed"]),
                "Vehicles": s["vehicles"],
            } for s in congestion[:20]]),
                use_container_width=True,
                column_config={"Congestion": st.column_config.ProgressColumn("Congestion", min_value=0, max_value=1, format="%.0f%%")},
            )

# ═══════════════════════════════════════
# TAB: Conversations
# ═══════════════════════════════════════
if "comms" in tabs:
    with tabs["comms"]:
        convos = api_get("/api/communication/conversations?limit=20")
        if convos:
            section_header("💬", f"Recent Conversations ({len(convos)})")
            for c in convos:
                with st.expander(f"💬 {c['channel'].upper()} — {c['topic'][:60]}"):
                    cc1, cc2 = st.columns([3, 1])
                    cc1.write(f"**Topic:** {c['topic']}")
                    cc2.write(f"**Participants:** {len(c['participants'])}")
                    if c.get("location"):
                        st.caption(f"📍 {c['location']}")
        else:
            st.info("No conversations yet. Start the simulation.")

        feed = api_get("/api/communication/social-feed?limit=15")
        if feed:
            section_header("📱", "Social Feed")
            feed_citizens = api_get("/api/citizens/?limit=1200") or []
            feed_citizen_by_id = {c["id"]: c for c in feed_citizens}

            for post in feed:
                sentiment_icon = {"positive": "😊", "neutral": "😐", "negative": "😟"}.get(post.get("sentiment", ""), "")
                tags = " ".join(f"`#{t}`" for t in post.get("tags", []))
                author = feed_citizen_by_id.get(post.get("author_id", ""))
                author_name = author["name"] if author else "Someone"
                author_avatar = citizen_avatar(author.get("gender", ""), author.get("age", 30)) if author else "🧑"

                comments_html = ""
                for c in post.get("comments", []):
                    c_author = feed_citizen_by_id.get(c.get("author_id", ""))
                    c_name = c_author["name"] if c_author else "Someone"
                    c_avatar = citizen_avatar(c_author.get("gender", ""), c_author.get("age", 30)) if c_author else "🧑"
                    comments_html += (
                        f'<div style="margin:6px 0 0 1.2rem;padding:6px 10px;border-left:2px solid rgba(124,108,246,0.3);">'
                        f'<span style="font-size:0.82rem;">{c_avatar} <strong>{c_name}</strong> {c["content"]}</span> '
                        f'<span class="meta">❤️ {c.get("likes",0)}</span></div>'
                    )

                st.markdown(
                    f'<div class="feed-card">'
                    f'<div class="author">{author_avatar} {author_name}</div>'
                    f'<div class="content">{sentiment_icon} {post["content"]}</div>'
                    f'<div class="meta">❤️ {post.get("likes", 0)} &nbsp; 🔄 {post.get("shares", 0)} &nbsp; {tags}</div>'
                    f'{comments_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

# ═══════════════════════════════════════
# TAB: Government
# ═══════════════════════════════════════
if "gov" in tabs:
    with tabs["gov"]:
        budgets = api_get("/api/government/budgets")
        if budgets:
            section_header("🏛", "Department Budgets")
            st.bar_chart({b["department"]: b["budget"] for b in budgets}, height=250)

            st.dataframe(pd.DataFrame([{
                "Department": b.get("name", ""),
                "Budget": round(b.get("budget", 0)),
                "Efficiency": round(b.get("efficiency", 0), 2),
                "Employees": b.get("employees", 0),
            } for b in budgets]),
                use_container_width=True,
                column_config={
                    "Budget": st.column_config.NumberColumn("Budget", format="$%.0f"),
                    "Efficiency": st.column_config.ProgressColumn("Efficiency", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

        policies = api_get("/api/government/policies")
        if policies:
            section_header("📋", f"Active Policies ({len(policies)})")
            for p in policies:
                with st.expander(f"📋 {p['name']} ({p['department']})"):
                    st.write(p.get("description", ""))
                    st.progress(p.get("approval_rating", 0), text=f"Approval: {pct(p.get('approval_rating', 0))}")

# ═══════════════════════════════════════
# TAB: Social Network
# ═══════════════════════════════════════
if "social" in tabs:
    with tabs["social"]:
        rel_stats = api_get("/api/relationships/stats")
        if rel_stats:
            section_header("🤝", "Social Network")
            r1, r2, r3 = st.columns(3)
            with r1:
                metric_card("Relationships", str(rel_stats.get("total_relationships", 0)), "blue")
            with r2:
                metric_card("Avg Trust", pct(rel_stats.get("avg_trust", 0)), "green")
            with r3:
                metric_card("Avg Closeness", pct(rel_stats.get("avg_closeness", 0)), "purple")

            by_type = rel_stats.get("by_type", {})
            if by_type:
                st.bar_chart(by_type, height=200)

        section_header("🔍", "Citizen Social Graph")
        citizens_list = api_get("/api/citizens/?limit=20")
        if citizens_list:
            names = {c["name"]: c["id"] for c in citizens_list}
            selected_name = st.selectbox("Select citizen", list(names.keys()))
            if selected_name and st.button("View Graph", use_container_width=False):
                cid = names[selected_name]
                graph = api_get(f"/api/relationships/citizens/{cid}/graph")
                if graph:
                    st.write(f"**{selected_name}** — {len(graph.get('edges', []))} connections")
                    for edge in graph.get("edges", []):
                        node = next((n for n in graph["nodes"] if n["id"] == edge["to"]), None)
                        label = node["label"] if node else edge["to"][:8]
                        trust_pct = pct(edge["trust"])
                        close_pct = pct(edge["closeness"])
                        st.write(f"  → **{label}** — `{edge['type']}` (trust: {trust_pct}, closeness: {close_pct})")

# ═══════════════════════════════════════
# TAB: Map
# ═══════════════════════════════════════
if "map" in tabs:
    with tabs["map"]:
        city_map = api_get("/api/city/map")
        if city_map:
            districts = city_map.get("districts", [])
            locations = city_map.get("locations", [])
            section_header("🗺️", f"City Map — {len(districts)} Districts, {len(locations)} Locations")

            map_citizens = api_get("/api/citizens/?limit=1200") or []
            map_conversations = api_get("/api/communication/conversations?limit=40") or []

            render_live_city_map(map_citizens, districts, map_conversations)
            st.caption("Dots glide to their new position each refresh • color = happiness • gold dashed line = an active face-to-face conversation • hover a dot for details.")

            for d in districts:
                safety_color = "🟢" if d["safety"] > 0.7 else ("🟡" if d["safety"] > 0.4 else "🔴")
                wealth_color = "🟢" if d["wealth"] > 0.7 else ("🟡" if d["wealth"] > 0.4 else "🔴")
                with st.expander(f"📍 {d['name']}  {safety_color} Safety {pct(d['safety'])}  {wealth_color} Wealth {pct(d['wealth'])}"):
                    st.caption(f"Center: ({d['center'][0]}, {d['center'][1]})  •  Radius: {d['radius']}")
                    dlocs = [
                        loc for loc in locations
                        if abs(loc["position"][0] - d["center"][0]) < d["radius"]
                        and abs(loc["position"][1] - d["center"][1]) < d["radius"]
                    ]
                    if dlocs:
                        st.dataframe(pd.DataFrame([{
                            "Name": loc["name"], "Type": loc["type"]
                        } for loc in dlocs[:15]]), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════
# TAB: Events
# ═══════════════════════════════════════
if "events" in tabs:
    with tabs["events"]:
        events = api_get("/api/events/?active_only=false")
        if events:
            active = [e for e in events if e.get("is_active")]
            section_header("⚡", f"Active Events ({len(active)})")
            if active:
                for e in active:
                    level = e.get("severity", "low")
                    location = "🌆 city-wide" if e.get("is_citywide") else f"📍 ({e.get('affected_area_x', 0):.0f}, {e.get('affected_area_y', 0):.0f}) r={e.get('affected_radius', 0):.0f}m"
                    alert_card(
                        f"<strong>{e['name']}</strong> ({level}) — {e['description']} — "
                        f"{e['remaining_ticks']} ticks remaining — {location}",
                        level=level,
                    )
            else:
                st.info("No active events.")

            past = [e for e in events if not e.get("is_active")]
            if past:
                section_header("📜", "Event History")
                st.dataframe(pd.DataFrame([{
                    "Name": e["name"], "Category": e["category"],
                    "Severity": e["severity"],
                } for e in past]), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════
# TAB: Disasters
# ═══════════════════════════════════════
if "disasters" in tabs:
    with tabs["disasters"]:
        active_disasters = api_get("/api/disasters/active")
        section_header("🌋", "Active Disasters")
        if active_disasters:
            for d in active_disasters:
                phase_colors = {"onset": "🟡", "peak": "🔴", "declining": "🟠", "recovery": "🟢", "resolved": "⚪"}
                icon = phase_colors.get(d["phase"], "⚪")
                alert_card(
                    f"{icon} <strong>{d['name']}</strong> — Phase: {d['phase'].upper()} "
                    f"| Intensity: {pct(d['intensity'])} | Radius: {d['radius']:.0f}m",
                    level="critical" if d["phase"] == "peak" else "high" if d["phase"] == "onset" else "medium",
                )
                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    metric_card("Casualties", str(d["casualties"]), "red")
                with d2:
                    metric_card("Injuries", str(d["injuries"]), "orange")
                with d3:
                    metric_card("Bldgs Damaged", str(d["buildings_damaged"]), "orange")
                with d4:
                    metric_card("Evacuated", str(d["evacuated"]), "blue")
                st.progress(d["progress"], text=f"Progress: {pct(d['progress'])}")
                st.caption(f"Economic damage: {dollar(d['economic_damage'])}")
                st.write("")
        else:
            st.info("No active disasters. Trigger one from the sidebar.")

        disaster_history = api_get("/api/disasters/history")
        if disaster_history:
            section_header("📜", "Disaster History")
            st.dataframe(pd.DataFrame([{
                "Name": d["name"], "Type": d["type"], "Phase": d["phase"],
                "Max Intensity": round(d["max_intensity"], 2),
                "Casualties": d["casualties"], "Injuries": d["injuries"],
                "Econ Damage": round(d["economic_damage"]),
                "Active": d["is_active"],
            } for d in disaster_history]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Max Intensity": st.column_config.ProgressColumn("Max Intensity", min_value=0, max_value=1, format="%.0f%%"),
                    "Econ Damage": st.column_config.NumberColumn("Econ Damage", format="$%.0f"),
                },
            )

# ═══════════════════════════════════════
# TAB: Pandemic
# ═══════════════════════════════════════
if "pandemic" in tabs:
    with tabs["pandemic"]:
        pandemic_stats = api_get("/api/pandemic/stats")
        if pandemic_stats:
            for p in pandemic_stats:
                is_active = p["is_active"]
                section_header("🦠" if is_active else "✅", f"{p['name']} ({p['pathogen']})")

                p1, p2, p3, p4 = st.columns(4)
                with p1:
                    metric_card("Total Cases", str(p["total_cases"]), "orange")
                with p2:
                    metric_card("Active Cases", str(p["active_cases"]), "red" if p["active_cases"] > 0 else "green")
                with p3:
                    metric_card("Recovered", str(p["recovered"]), "green")
                with p4:
                    metric_card("Deaths", str(p["deaths"]), "red")

                p5, p6, p7, p8 = st.columns(4)
                with p5:
                    metric_card("Vaccinated", str(p["vaccinated"]), "teal")
                with p6:
                    hosp_pct = p["hospitalized"] / max(p["hospital_capacity"], 1)
                    metric_card("Hospital", f"{p['hospitalized']}/{p['hospital_capacity']}", "red" if hosp_pct > 0.8 else "orange")
                with p7:
                    metric_card("Mortality", f"{p['mortality_rate_pct']:.2f}%", "red")
                with p8:
                    metric_card("R0", str(p["r0"]), "purple")

                if is_active:
                    status_badges = []
                    if p["lockdown_active"]:
                        status_badges.append("🔒 Lockdown")
                    if p["mask_mandate"]:
                        status_badges.append("😷 Masks")
                    if p["vaccination_available"]:
                        status_badges.append("💉 Vaccinating")
                    if status_badges:
                        st.info(" | ".join(status_badges))

                    ctl1, ctl2, ctl3 = st.columns(3)
                    with ctl1:
                        lbl = "🔓 End Lockdown" if p["lockdown_active"] else "🔒 Lockdown"
                        if st.button(lbl, key=f"lock_{p['id']}", use_container_width=True):
                            api_post("/api/pandemic/lockdown", {"pandemic_id": p["id"], "active": not p["lockdown_active"]})
                            st.rerun()
                    with ctl2:
                        lbl = "😷 End Masks" if p["mask_mandate"] else "😷 Masks"
                        if st.button(lbl, key=f"mask_{p['id']}", use_container_width=True):
                            api_post("/api/pandemic/mask-mandate", {"pandemic_id": p["id"], "active": not p["mask_mandate"]})
                            st.rerun()
                    with ctl3:
                        if not p["vaccination_available"]:
                            if st.button("💉 Vaccinate", key=f"vax_{p['id']}", use_container_width=True):
                                api_post("/api/pandemic/vaccinate", {"pandemic_id": p["id"], "rate": 0.02})
                                st.rerun()
                        else:
                            st.success("💉 Active")
                st.markdown("---")
        else:
            st.info("No pandemics. Start one from the sidebar.")

# ═══════════════════════════════════════
# TAB: Elections
# ═══════════════════════════════════════
if "elections" in tabs:
    with tabs["elections"]:
        elections = api_get("/api/elections/")
        if elections:
            for e in elections:
                phase_icon = {"announcement": "📢", "campaigning": "📣", "debate": "🎤", "voting": "🗳", "counting": "📊", "completed": "✅"}.get(e["phase"], "🗳")
                section_header(phase_icon, f"{e['name']} — {e['phase'].upper()}")

                e1, e2, e3 = st.columns(3)
                with e1:
                    metric_card("Total Voters", str(e["total_voters"]), "blue")
                with e2:
                    metric_card("Votes Cast", str(e["votes_cast"]), "purple")
                with e3:
                    metric_card("Turnout", pct(e["turnout_rate"]), "green" if e["turnout_rate"] > 0.5 else "orange")

                if e.get("winner"):
                    st.success(f"🏆 **Winner: {e['winner']}**")

                if e.get("candidates"):
                    cand_df = pd.DataFrame([{
                        "Name": c["name"] + (" 🏆" if c["is_winner"] else ""),
                        "Party": c["party"],
                        "Slogan": c["slogan"],
                        "Popularity": round(c["popularity"], 2),
                        "Votes": c["votes"],
                        "Vote Share": round(c["vote_share"], 3),
                    } for c in e["candidates"]])
                    st.dataframe(cand_df, use_container_width=True, hide_index=True,
                        column_config={
                            "Popularity": st.column_config.ProgressColumn("Popularity", min_value=0, max_value=1, format="%.0f%%"),
                            "Vote Share": st.column_config.ProgressColumn("Vote Share", min_value=0, max_value=1, format="%.1f%%"),
                        })

                    votes = {c["name"]: c["votes"] for c in e["candidates"]}
                    if sum(votes.values()) > 0:
                        st.bar_chart(votes, height=200)
                st.markdown("---")
        else:
            st.info("No elections. Start one from the sidebar.")

# ═══════════════════════════════════════
# TAB: Social Media
# ═══════════════════════════════════════
if "social_media" in tabs:
    with tabs["social_media"]:
        trending = api_get("/api/social-media/trending")
        section_header("📈", "Trending Topics")
        if trending:
            for t in trending:
                misinfo = " ⚠️ `MISINFO`" if t.get("is_misinformation") else ""
                sent_icon = "😊" if t["sentiment"] > 0.1 else ("😟" if t["sentiment"] < -0.1 else "😐")
                st.markdown(
                    f'<div class="feed-card">'
                    f'<div class="author">#{t["hashtag"]}{misinfo}</div>'
                    f'<div class="content">{t["topic"]}</div>'
                    f'<div class="meta">'
                    f'{sent_icon} Sentiment: {t["sentiment"]:.2f} &nbsp; '
                    f'📊 Mentions: {t["mentions"]} (peak: {t["peak_mentions"]}) &nbsp; '
                    f'🔥 Virality: {pct(t["virality"])}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No trending data yet. Start the simulation.")

        shifts = api_get("/api/social-media/opinion-shifts?limit=20")
        if shifts:
            section_header("🔄", "Opinion Shifts")
            st.dataframe(pd.DataFrame([{
                "Citizen": s["citizen_id"][:8],
                "Topic": s["topic"],
                "Before": round(s["old_opinion"], 3),
                "After": round(s["new_opinion"], 3),
                "Source": s["influence_source"],
            } for s in shifts]), use_container_width=True, hide_index=True)

        section_header("🗞", "Launch Custom Topic")
        lc1, lc2 = st.columns(2)
        with lc1:
            custom_hashtag = st.text_input("Hashtag", "CustomTopic", key="sm_ht")
        with lc2:
            custom_topic = st.text_input("Description", "A custom trending topic", key="sm_tp")
        custom_cat = st.selectbox("Category", ["news", "entertainment", "politics", "economy", "health", "disaster", "sports", "community"], key="sm_cat")
        if st.button("📢 Launch", key="sm_launch", use_container_width=True):
            r = api_post("/api/social-media/trigger-topic", {"hashtag": custom_hashtag, "topic": custom_topic, "category": custom_cat, "initial_mentions": 20})
            if r:
                st.toast(f"Topic #{r['hashtag']} launched!", icon="📢")
                st.rerun()

# ═══════════════════════════════════════
# TAB: AI Advisor
# ═══════════════════════════════════════
if "advisor" in tabs:
    with tabs["advisor"]:
        advisor_status = api_get("/api/ai-advisor/status")
        if advisor_status:
            section_header("🤖", "AI City Advisor")
            a1, a2, a3 = st.columns(3)
            with a1:
                avail = advisor_status.get("available", False)
                metric_card("Status", "Online" if avail else "Offline", "green" if avail else "red")
            with a2:
                metric_card("Provider", advisor_status.get("provider", "none").title(), "blue")
            with a3:
                metric_card("Model", advisor_status.get("model", "n/a"), "purple")

        section_header("📊", "City Analysis")
        if st.button("Run Full Analysis", key="adv_analyze", use_container_width=True):
            with st.spinner("AI is analyzing the city..."):
                analysis = api_get("/api/ai-advisor/analyze")
                if analysis:
                    risk_map = {"low": ("🟢", "green"), "moderate": ("🟡", "orange"), "high": ("🟠", "red"), "critical": ("🔴", "red")}
                    risk = analysis.get("risk_level", "low")
                    r_icon, r_color = risk_map.get(risk, ("⚪", "blue"))
                    alert_card(
                        f"<strong>Risk: {r_icon} {risk.upper()}</strong><br>"
                        f"{analysis.get('overall_assessment', '')}<br>"
                        f"<em>Priority: {analysis.get('action_priority', '')}</em>",
                        level=risk if risk in ("low", "medium", "high", "critical") else "low",
                    )

                    if analysis.get("top_issues"):
                        for issue in analysis["top_issues"]:
                            sev = issue.get("severity", "low")
                            with st.expander(f"{'🔴' if sev in ('high','critical') else '🟡'} {issue['issue']}"):
                                st.write(f"**Metric:** {issue.get('metric', '')}")
                                st.write(f"**Recommendation:** {issue.get('recommendation', '')}")
                                st.write(f"**Expected Impact:** {issue.get('expected_impact', '')}")

                    if analysis.get("positive_trends"):
                        for t in analysis["positive_trends"]:
                            st.success(f"✅ {t}")

        st.markdown("---")
        section_header("📝", "City Report")
        if st.button("Generate Report", key="adv_report", use_container_width=True):
            with st.spinner("Writing report..."):
                report = api_get("/api/ai-advisor/report")
                if report:
                    st.markdown(report.get("report", ""))

        st.markdown("---")
        section_header("🔮", "What-If Scenario")
        st.caption(
            "Preset scenarios below compute real numbers from the simulation's own formulas "
            "(police staffing → crime-solving math, tax rate → salary withholding, or the same "
            "location-scoring model the 3D Build Mode preview uses) — not an AI guess. "
            "The AI only writes the plain-language summary of numbers already computed here."
        )

        st.session_state.setdefault("whatif_results", [])
        presets = api_get("/api/ai-advisor/whatif/presets") or []

        if presets:
            preset_cols = st.columns(3)
            for i, preset in enumerate(presets):
                with preset_cols[i % 3]:
                    if st.button(f"{preset['icon']} {preset['name']}", key=f"whatif_pick_{preset['key']}", use_container_width=True):
                        st.session_state["whatif_selected_preset"] = preset["key"]

        selected_key = st.session_state.get("whatif_selected_preset")
        selected_preset = next((p for p in presets if p["key"] == selected_key), None)
        if selected_preset:
            with st.container(border=True):
                st.markdown(f"**{selected_preset['icon']} {selected_preset['name']}**")
                param_values = {}
                for param in selected_preset["params"]:
                    if param["type"] == "percent":
                        val = st.slider(param["label"], min_value=float(param["min"]) * 100, max_value=float(param["max"]) * 100,
                                         value=float(param["default"]) * 100, step=float(param["step"]) * 100,
                                         key=f"whatif_param_{selected_key}_{param['name']}", format="%.0f%%")
                        param_values[param["name"]] = val / 100
                    elif param["type"] == "int":
                        param_values[param["name"]] = st.slider(param["label"], min_value=int(param["min"]), max_value=int(param["max"]),
                                                                  value=int(param["default"]), step=int(param["step"]),
                                                                  key=f"whatif_param_{selected_key}_{param['name']}")
                    else:
                        param_values[param["name"]] = st.number_input(param["label"], min_value=float(param["min"]), max_value=float(param["max"]),
                                                                        value=float(param["default"]), step=float(param["step"]),
                                                                        key=f"whatif_param_{selected_key}_{param['name']}")

                run_col, clear_col = st.columns([3, 1])
                with run_col:
                    if st.button("▶ Run Scenario", key="whatif_run_btn", use_container_width=True, type="primary"):
                        with st.spinner("Computing grounded projection... (the AI narrative step can take a while on CPU)"):
                            # api_post's default 10s timeout is too short here — the numeric
                            # projection is instant, but the LLM narrative call on top of it
                            # can run well past 10s on Ollama, and a timeout inside api_post
                            # is swallowed into a silent None with no error shown.
                            try:
                                resp = httpx.post(
                                    f"{API_BASE}/api/ai-advisor/whatif/run",
                                    json={"key": selected_key, "params": param_values},
                                    timeout=90,
                                )
                                resp.raise_for_status()
                                result = resp.json()
                            except Exception as err:
                                st.error(f"Scenario run failed: {err}")
                                result = None
                            if result and not result.get("error"):
                                st.session_state["whatif_results"].append(result)
                                st.session_state["whatif_results"] = st.session_state["whatif_results"][-3:]
                            elif result:
                                st.error(result["error"])
                with clear_col:
                    if st.button("✕ Clear All", key="whatif_clear_btn", use_container_width=True):
                        st.session_state["whatif_results"] = []

        def _render_whatif_card(result: dict):
            badge = "📊 DATA-GROUNDED" if result.get("grounded") else "🤖 AI ESTIMATE"
            st.markdown(f"##### {result.get('title', 'Scenario')}")
            st.caption(badge)
            for a in result.get("assumptions", []):
                st.caption(f"ℹ️ {a}")
            if result.get("narrative"):
                st.write(result["narrative"])
            if result.get("deltas"):
                for k, v in result["deltas"].items():
                    st.write(f"• **{k.replace('_', ' ').title()}:** {v}")
            if result.get("cost") is not None:
                st.write(f"• **Cost:** ${result['cost']:,.0f}")

        results = st.session_state["whatif_results"]
        if len(results) == 1:
            with st.container(border=True):
                _render_whatif_card(results[0])
        elif len(results) > 1:
            st.markdown(f"**Comparing {len(results)} scenarios:**")
            cmp_cols = st.columns(len(results))
            for col, result in zip(cmp_cols, results):
                with col:
                    with st.container(border=True):
                        _render_whatif_card(result)

        st.markdown("---")
        section_header("💭", "Custom Scenario")
        st.caption("🤖 AI ESTIMATE — free text, no grounded formula exists for arbitrary scenarios.")
        scenario_text = st.text_area("Describe a scenario", placeholder="e.g., What if we double police funding?", key="adv_scenario")
        if st.button("Analyze", key="adv_scenario_btn", use_container_width=True) and scenario_text:
            with st.spinner("Analyzing scenario..."):
                sr = api_post("/api/ai-advisor/scenario", {"scenario": scenario_text})
                if sr:
                    rec_map = {"proceed": "🟢 PROCEED", "modify": "🟡 MODIFY", "reject": "🔴 REJECT"}
                    st.write(f"**Feasible:** {'Yes' if sr.get('feasible') else 'No'}")
                    st.write(f"**Recommendation:** {rec_map.get(sr.get('recommendation', ''), sr.get('recommendation', ''))}")
                    st.write(f"**Analysis:** {sr.get('analysis', '')}")
                    if sr.get("projected_impacts"):
                        st.write("**Projected Impacts:**")
                        for k, v in sr["projected_impacts"].items():
                            st.write(f"  • **{k.title()}:** {v}")
                    if sr.get("risks"):
                        for r in sr["risks"]:
                            st.warning(f"⚠️ {r}")

        st.markdown("---")
        section_header("💬", "Ask Anything")
        question = st.text_input("Ask about the city", placeholder="e.g., Why is stress increasing?", key="adv_q")
        if st.button("Ask", key="adv_ask") and question:
            with st.spinner("Thinking..."):
                ans = api_post("/api/ai-advisor/ask", {"question": question})
                if ans:
                    st.markdown(ans.get("answer", ""))

# ═══════════════════════════════════════
# TAB: Graph Insights
# ═══════════════════════════════════════
if "graph" in tabs:
    with tabs["graph"]:
        graph_st = api_get("/api/graph/status")
        section_header("🔗", "Graph Intelligence")
        if graph_st:
            g1, g2, g3, g4, g5 = st.columns(5)
            with g1:
                metric_card("Status", "Online" if graph_st.get("available") else "Offline", "green" if graph_st.get("available") else "red")
            with g2:
                metric_card("Nodes", str(graph_st.get("nodes", 0)), "blue")
            with g3:
                metric_card("Edges", str(graph_st.get("edges", 0)), "purple")
            with g4:
                metric_card("Avg Degree", str(graph_st.get("avg_degree", 0)), "teal")
            with g5:
                metric_card("Max Degree", str(graph_st.get("max_degree", 0)), "orange")

        if st.button("🔄 Sync from Database", key="graph_sync", use_container_width=True):
            with st.spinner("Syncing graph..."):
                r = api_post("/api/graph/sync")
                if r and "error" not in r:
                    st.toast(f"Synced {r.get('synced_citizens', 0)} citizens, {r.get('synced_relationships', 0)} relationships", icon="✅")
                    st.rerun()
                elif r:
                    st.error(r.get("error", ""))

        influencers = api_get("/api/graph/influencers?limit=10")
        if influencers:
            section_header("🌟", "Top Influencers")
            st.dataframe(pd.DataFrame([{
                "Rank": i + 1,
                "Name": inf.get("name", ""),
                "Occupation": inf.get("occupation", ""),
                "Connections": inf.get("connections", 0),
                "Avg Trust": round(inf.get("avg_trust", 0), 2),
                "Influence": round(inf.get("influence_score", 0), 2),
            } for i, inf in enumerate(influencers)]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Avg Trust": st.column_config.ProgressColumn("Avg Trust", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

        section_header("🔍", "Find Shortest Path")
        citizens_for_path = api_get("/api/citizens/?limit=30")
        if citizens_for_path:
            names_p = {c["name"]: c["id"] for c in citizens_for_path}
            nl = list(names_p.keys())
            pc1, pc2 = st.columns(2)
            with pc1:
                from_n = st.selectbox("From", nl, key="gp_from")
            with pc2:
                to_n = st.selectbox("To", nl, key="gp_to")
            if st.button("Find Path", key="gp_find") and from_n != to_n:
                pr = api_get(f"/api/graph/shortest-path/{names_p[from_n]}/{names_p[to_n]}")
                if pr and "error" not in pr:
                    path_names = [n["name"] for n in pr["path"]]
                    st.success(f"**{pr['distance']} hops:** {' → '.join(path_names)}")
                else:
                    st.warning("No path found.")

        district_conns = api_get("/api/graph/district-connections")
        if district_conns:
            section_header("🏘", "Inter-District Connections")
            st.dataframe(pd.DataFrame(district_conns), use_container_width=True, hide_index=True)

        section_header("🧠", "Vector Memory Search")
        vm_st = api_get("/api/vector-memory/status")
        if vm_st:
            vm1, vm2 = st.columns(2)
            with vm1:
                metric_card("Vector Store", "Online" if vm_st.get("available") else "Offline", "green" if vm_st.get("available") else "red")
            with vm2:
                metric_card("Stored Memories", str(vm_st.get("points_count", 0)), "purple")

        sq = st.text_input("Semantic search", placeholder="e.g., felt happy at the park", key="vs_q")
        if st.button("Search Memories", key="vs_btn") and sq:
            sr = api_post("/api/vector-memory/search", {"query": sq, "limit": 10, "min_score": 0.4})
            if sr and sr.get("results"):
                for m in sr["results"]:
                    st.write(f"**{pct(m['score'])}** — {m['content']}  `{m['memory_type']}` importance: {pct(m['importance'])}")
            else:
                st.info("No results. Index memories first.")

# ═══════════════════════════════════════
# TAB: Weather
# ═══════════════════════════════════════
if "weather" in tabs:
    with tabs["weather"]:
        weather = api_get("/api/weather/current")
        if weather:
            section_header("🌤", f"Current Weather — {weather['season'].title()}")
            condition_icons = {"clear": "☀️", "cloudy": "☁️", "rain": "🌧", "storm": "⛈",
                              "snow": "❄️", "fog": "🌫", "heatwave": "🔥", "cold_snap": "🥶"}
            icon = condition_icons.get(weather["condition"], "🌤")

            w1, w2, w3, w4, w5, w6 = st.columns(6)
            with w1:
                metric_card("Condition", f"{icon} {weather['condition'].replace('_', ' ').title()}", "blue")
            with w2:
                metric_card("Temperature", f"{weather['temperature_c']}°C", "orange" if weather["temperature_c"] > 30 else "teal")
            with w3:
                metric_card("Humidity", pct(weather["humidity"]), "blue")
            with w4:
                metric_card("Wind", f"{weather['wind_speed_kmh']} km/h", "purple")
            with w5:
                metric_card("Visibility", f"{weather['visibility_km']} km", "green")
            with w6:
                metric_card("AQI", str(weather["air_quality_index"]), "red" if weather["air_quality_index"] > 100 else "green")

            section_header("📊", "Weather Effects on City")
            e1, e2, e3, e4 = st.columns(4)
            with e1:
                h_mod = weather["happiness_modifier"]
                metric_card("Happiness", f"{'+' if h_mod >= 0 else ''}{h_mod:.2f}", "green" if h_mod >= 0 else "red")
            with e2:
                hm = weather["health_modifier"]
                metric_card("Health", f"{'+' if hm >= 0 else ''}{hm:.2f}", "green" if hm >= 0 else "red")
            with e3:
                metric_card("Traffic", f"{weather['traffic_modifier']:.1f}x", "orange" if weather["traffic_modifier"] > 1.2 else "green")
            with e4:
                metric_card("Crime", f"{weather['crime_modifier']:.1f}x", "red" if weather["crime_modifier"] > 1.1 else "green")

        weather_hist = api_get("/api/weather/history?limit=30")
        if weather_hist and len(weather_hist) > 1:
            section_header("📈", "Weather History")
            wh_df = pd.DataFrame(weather_hist)
            if "temperature_c" in wh_df.columns:
                st.line_chart(wh_df["temperature_c"].values, height=180)
                st.caption("Temperature over recent ticks")

# ═══════════════════════════════════════
# TAB: Crime
# ═══════════════════════════════════════
if "crime" in tabs:
    with tabs["crime"]:
        crime_stats = api_get("/api/crime/stats")
        if crime_stats:
            section_header("🚔", "Crime Dashboard")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                metric_card("Total Crimes", str(crime_stats.get("total_crimes", 0)), "red")
            with c2:
                metric_card("Solved", str(crime_stats.get("solved", 0)), "green")
            with c3:
                metric_card("Unsolved", str(crime_stats.get("unsolved", 0)), "orange")
            with c4:
                metric_card("Solve Rate", pct(crime_stats.get("solve_rate", 0)), "blue")

            by_type = crime_stats.get("by_type", {})
            if by_type:
                section_header("📊", "Crimes by Type")
                st.bar_chart(by_type, height=200)

            total_damage = crime_stats.get("total_economic_damage", 0)
            if total_damage:
                st.caption(f"Total economic damage: {dollar(total_damage)}")

        recent_crimes = api_get("/api/crime/recent?limit=15")
        if recent_crimes:
            section_header("📋", "Recent Incidents")
            for cr in recent_crimes:
                sev_color = {"minor": "low", "moderate": "medium", "serious": "high", "severe": "critical"}
                alert_card(
                    f"<strong>{cr['crime_type'].replace('_', ' ').title()}</strong> ({cr['severity']}) — "
                    f"{cr['description']} — Damage: {dollar(cr['economic_damage'])} — "
                    f"{'✅ Solved' if cr['is_solved'] else '🔍 Under investigation'}",
                    level=sev_color.get(cr["severity"], "low"),
                )

        police = api_get("/api/crime/police")
        if police:
            section_header("👮", "Police Units")
            st.dataframe(pd.DataFrame([{
                "Station": u["name"],
                "Officers": u["officers"],
                "Effectiveness": round(u["effectiveness"], 2),
                "Cases Solved": u["cases_solved"],
            } for u in police]),
                use_container_width=True, hide_index=True,
                column_config={"Effectiveness": st.column_config.ProgressColumn("Effectiveness", min_value=0, max_value=1, format="%.0f%%")},
            )

# ═══════════════════════════════════════
# TAB: Healthcare
# ═══════════════════════════════════════
if "health" in tabs:
    with tabs["health"]:
        health_stats = api_get("/api/healthcare/stats")
        if health_stats:
            section_header("🏥", "Healthcare Overview")
            h1, h2, h3, h4, h5 = st.columns(5)
            with h1:
                metric_card("Hospitals", str(health_stats.get("hospitals", 0)), "blue")
            with h2:
                metric_card("Total Beds", str(health_stats.get("total_beds", 0)), "teal")
            with h3:
                metric_card("Occupied", str(health_stats.get("occupied_beds", 0)), "orange")
            with h4:
                occ_rate = health_stats.get("occupancy_rate", 0)
                metric_card("Occupancy", pct(occ_rate), "red" if occ_rate > 0.8 else "green")
            with h5:
                metric_card("Active Cases", str(health_stats.get("active_conditions", 0)), "red")

        hospitals = api_get("/api/healthcare/hospitals")
        if hospitals:
            section_header("🏨", "Hospitals")
            st.dataframe(pd.DataFrame([{
                "Name": h["name"],
                "Type": h["type"].title(),
                "Beds": f"{h['occupied_beds']}/{h['total_beds']}",
                "ICU": f"{h['icu_occupied']}/{h['icu_beds']}",
                "Staff": h["staff_count"],
                "Quality": round(h["quality_rating"], 2),
                "Occupancy": round(h["occupancy_rate"], 2),
            } for h in hospitals]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Quality": st.column_config.ProgressColumn("Quality", min_value=0, max_value=1, format="%.0f%%"),
                    "Occupancy": st.column_config.ProgressColumn("Occupancy", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

        records = api_get("/api/healthcare/records?limit=15")
        if records:
            section_header("📋", "Recent Medical Records")
            st.dataframe(pd.DataFrame([{
                "Condition": r["condition"].replace("_", " ").title(),
                "Type": r["condition_type"].title(),
                "Severity": round(r["severity"], 2),
                "Hospitalized": "Yes" if r["is_hospitalized"] else "No",
                "Resolved": "Yes" if r["is_resolved"] else "No",
                "Cost": round(r["treatment_cost"]),
            } for r in records]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Severity": st.column_config.ProgressColumn("Severity", min_value=0, max_value=1, format="%.0f%%"),
                    "Cost": st.column_config.NumberColumn("Cost", format="$%.0f"),
                },
            )

# ═══════════════════════════════════════
# TAB: Education
# ═══════════════════════════════════════
if "edu" in tabs:
    with tabs["edu"]:
        edu_stats = api_get("/api/education/stats")
        if edu_stats:
            section_header("🎓", "Education Overview")
            e1, e2, e3, e4 = st.columns(4)
            with e1:
                metric_card("Schools", str(edu_stats.get("schools", 0)), "blue")
            with e2:
                metric_card("Enrolled", str(edu_stats.get("active_enrollments", 0)), "purple")
            with e3:
                metric_card("Graduated", str(edu_stats.get("total_graduations", 0)), "green")
            with e4:
                metric_card("Skills Gained", str(edu_stats.get("total_skills", 0)), "teal")

        schools = api_get("/api/education/schools")
        if schools:
            section_header("🏫", "Schools & Universities")
            st.dataframe(pd.DataFrame([{
                "Name": s["name"],
                "Type": s["type"].replace("_", " ").title(),
                "Enrolled": f"{s['enrolled']}/{s['capacity']}",
                "Teachers": s["teachers"],
                "Quality": round(s["quality_rating"], 2),
                "Tuition": round(s["tuition"]),
                "Grad Rate": round(s["graduation_rate"], 2),
                "Programs": ", ".join(s.get("programs", [])),
            } for s in schools]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Quality": st.column_config.ProgressColumn("Quality", min_value=0, max_value=1, format="%.0f%%"),
                    "Grad Rate": st.column_config.ProgressColumn("Grad Rate", min_value=0, max_value=1, format="%.0f%%"),
                    "Tuition": st.column_config.NumberColumn("Tuition", format="$%.0f"),
                },
            )

        enrollments = api_get("/api/education/enrollments?limit=20")
        if enrollments:
            section_header("📚", "Active Enrollments")
            st.dataframe(pd.DataFrame([{
                "Citizen": e["citizen_id"][:8],
                "Program": e["program"].title(),
                "Progress": round(e["progress"], 2),
                "GPA": round(e["gpa"], 2),
            } for e in enrollments]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

# ═══════════════════════════════════════
# TAB: Housing
# ═══════════════════════════════════════
if "housing" in tabs:
    with tabs["housing"]:
        housing_stats = api_get("/api/housing/stats")
        if housing_stats:
            section_header("🏠", "Real Estate Market")
            h1, h2, h3, h4, h5 = st.columns(5)
            with h1:
                metric_card("Properties", str(housing_stats.get("total_properties", 0)), "blue")
            with h2:
                metric_card("Occupied", str(housing_stats.get("occupied", 0)), "green")
            with h3:
                metric_card("For Rent", str(housing_stats.get("for_rent", 0)), "orange")
            with h4:
                metric_card("Avg Rent", dollar(housing_stats.get("avg_rent", 0)), "purple")
            with h5:
                metric_card("Avg Value", dollar(housing_stats.get("avg_market_value", 0)), "teal")

            by_type = housing_stats.get("by_type", {})
            if by_type:
                st.bar_chart(by_type, height=200)

        properties = api_get("/api/housing/properties?limit=20")
        if properties:
            section_header("🏘", "Property Listings")
            st.dataframe(pd.DataFrame([{
                "Name": p["name"],
                "Type": p["type"].title(),
                "Size": f"{p['size_sqm']}m²",
                "Value": round(p["market_value"]),
                "Rent": round(p["monthly_rent"]),
                "Quality": round(p["quality"], 2),
                "Condition": round(p["condition"], 2),
                "Status": "Occupied" if p["is_occupied"] else ("For Rent" if p["is_for_rent"] else "Available"),
            } for p in properties]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Value": st.column_config.NumberColumn("Value", format="$%.0f"),
                    "Rent": st.column_config.NumberColumn("Rent", format="$%.0f/mo"),
                    "Quality": st.column_config.ProgressColumn("Quality", min_value=0, max_value=1, format="%.0f%%"),
                    "Condition": st.column_config.ProgressColumn("Condition", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

        txns = api_get("/api/housing/transactions?limit=10")
        if txns:
            section_header("📋", "Recent Transactions")
            st.dataframe(pd.DataFrame([{
                "Type": t["type"].replace("_", " ").title(),
                "Amount": round(t["amount"]),
            } for t in txns]),
                use_container_width=True, hide_index=True,
                column_config={"Amount": st.column_config.NumberColumn("Amount", format="$%.0f")},
            )

# ═══════════════════════════════════════
# TAB: News
# ═══════════════════════════════════════
if "news" in tabs:
    with tabs["news"]:
        news_stats = api_get("/api/news/stats")
        if news_stats:
            section_header("📰", "News & Media")
            n1, n2, n3, n4 = st.columns(4)
            with n1:
                metric_card("Articles", str(news_stats.get("total_articles", 0)), "blue")
            with n2:
                metric_card("Outlets", str(news_stats.get("outlets", 0)), "purple")
            with n3:
                metric_card("Total Views", str(news_stats.get("total_views", 0)), "green")
            with n4:
                metric_card("Breaking", str(news_stats.get("breaking_news", 0)), "red")

            by_cat = news_stats.get("by_category", {})
            if by_cat:
                st.bar_chart(by_cat, height=200)

        articles = api_get("/api/news/articles?limit=15")
        if articles:
            section_header("📋", "Latest Headlines")
            for a in articles:
                sentiment_icon = "🟢" if a["sentiment"] > 0.1 else ("🔴" if a["sentiment"] < -0.1 else "🟡")
                breaking = " 🔴 BREAKING" if a["is_breaking"] else ""
                st.markdown(
                    f'<div class="feed-card">'
                    f'<div class="author">{a["outlet"]} ({a["outlet_type"]}){breaking}</div>'
                    f'<div class="content"><strong>{a["headline"]}</strong></div>'
                    f'<div class="content">{a["summary"]}</div>'
                    f'<div class="meta">{sentiment_icon} Sentiment: {a["sentiment"]:.2f} &nbsp; '
                    f'👁 {a["views"]} views &nbsp; 📂 {a["category"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        outlets = api_get("/api/news/outlets")
        if outlets:
            section_header("📡", "News Outlets")
            st.dataframe(pd.DataFrame([{
                "Name": o["name"],
                "Type": o["type"].title(),
                "Bias": round(o["political_bias"], 2),
                "Credibility": round(o["credibility"], 2),
                "Reach": round(o["reach"], 2),
                "Sensationalism": round(o["sensationalism"], 2),
            } for o in outlets]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Credibility": st.column_config.ProgressColumn("Credibility", min_value=0, max_value=1, format="%.0f%%"),
                    "Reach": st.column_config.ProgressColumn("Reach", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

# ═══════════════════════════════════════
# TAB: Culture
# ═══════════════════════════════════════
if "culture" in tabs:
    with tabs["culture"]:
        culture_stats = api_get("/api/culture/stats")
        if culture_stats:
            section_header("🎭", "Culture & Entertainment")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1:
                metric_card("Venues", str(culture_stats.get("total_venues", 0)), "blue")
            with c2:
                metric_card("Open", str(culture_stats.get("open_venues", 0)), "green")
            with c3:
                metric_card("Visitors", str(culture_stats.get("total_visitors", 0)), "purple")
            with c4:
                metric_card("Daily Revenue", dollar(culture_stats.get("daily_revenue", 0)), "teal")
            with c5:
                metric_card("Active Festivals", str(culture_stats.get("active_festivals", 0)), "orange")
            with c6:
                metric_card("Total Festivals", str(culture_stats.get("total_festivals", 0)), "red")

        venues = api_get("/api/culture/venues")
        if venues:
            section_header("🏟", "Venues")
            st.dataframe(pd.DataFrame([{
                "Name": v["name"],
                "Type": v["type"].title(),
                "Capacity": v["capacity"],
                "Popularity": round(v["popularity"], 2),
                "Ticket": round(v["ticket_price"], 2),
                "Revenue": round(v["daily_revenue"]),
                "Total Visitors": v["total_visitors"],
                "Open": "Yes" if v["is_open"] else "No",
            } for v in venues]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Popularity": st.column_config.ProgressColumn("Popularity", min_value=0, max_value=1, format="%.0f%%"),
                    "Ticket": st.column_config.NumberColumn("Ticket", format="$%.2f"),
                    "Revenue": st.column_config.NumberColumn("Revenue", format="$%.0f"),
                },
            )

        festivals = api_get("/api/culture/festivals")
        if festivals:
            section_header("🎉", "Festivals & Events")
            for f in festivals:
                status = "🎊 ACTIVE" if f["is_active"] else "✅ Ended"
                alert_card(
                    f"<strong>{f['name']}</strong> ({f['type'].replace('_', ' ').title()}) — {status} — "
                    f"Attendees: {f['attendees']}/{f['max_attendees']} — "
                    f"Happiness Boost: +{f['happiness_boost']:.2f}",
                    level="low" if f["is_active"] else "medium",
                )

# ═══════════════════════════════════════
# TAB: Environment
# ═══════════════════════════════════════
if "environment" in tabs:
    with tabs["environment"]:
        env_stats = api_get("/api/environment/stats")
        if env_stats:
            section_header("🌳", "Environment & Sustainability")
            e1, e2, e3, e4 = st.columns(4)
            with e1:
                aqi = env_stats.get("air_quality_index", 0)
                metric_card("Air Quality", str(aqi), "red" if aqi > 100 else "green")
            with e2:
                metric_card("Water Quality", pct(env_stats.get("water_quality", 0)), "blue")
            with e3:
                metric_card("Noise Level", f"{env_stats.get('noise_level_db', 0)} dB", "orange")
            with e4:
                metric_card("Green Coverage", pct(env_stats.get("green_coverage_pct", 0)), "green")

            e5, e6, e7, e8 = st.columns(4)
            with e5:
                metric_card("Carbon Emissions", f"{env_stats.get('carbon_emissions_tons', 0):,.0f}t", "red")
            with e6:
                metric_card("Recycling Rate", pct(env_stats.get("recycling_rate", 0)), "teal")
            with e7:
                metric_card("Renewable Energy", pct(env_stats.get("renewable_energy_pct", 0)), "green")
            with e8:
                metric_card("Waste", f"{env_stats.get('waste_tons', 0):,.0f}t", "orange")

            i1, i2 = st.columns(2)
            with i1:
                metric_card("Active Initiatives", str(env_stats.get("active_initiatives", 0)), "purple")
            with i2:
                metric_card("Completed Initiatives", str(env_stats.get("completed_initiatives", 0)), "green")

        initiatives = api_get("/api/environment/initiatives")
        if initiatives:
            section_header("🌱", "Green Initiatives")
            st.dataframe(pd.DataFrame([{
                "Name": i["name"],
                "Type": i["type"].replace("_", " ").title(),
                "Cost": round(i["cost"]),
                "Progress": round(i["progress"], 2),
                "Carbon Impact": i["impact_carbon"],
                "Status": "Active" if i["is_active"] else ("Completed" if i["is_completed"] else "Inactive"),
            } for i in initiatives]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Cost": st.column_config.NumberColumn("Cost", format="$%.0f"),
                    "Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

# ═══════════════════════════════════════
# TAB: Demographics
# ═══════════════════════════════════════
if "demographics" in tabs:
    with tabs["demographics"]:
        demo_stats = api_get("/api/demographics/stats")
        if demo_stats:
            section_header("🧑‍🤝‍🧑", "Population Overview")
            d1, d2, d3, d4 = st.columns(4)
            with d1:
                metric_card("Population", str(demo_stats.get("total_population", 0)), "blue")
            with d2:
                metric_card("Avg Age", f"{demo_stats.get('avg_age', 0):.1f}", "teal")
            with d3:
                metric_card("Dependency Ratio", f"{demo_stats.get('dependency_ratio', 0):.2f}", "orange")
            with d4:
                metric_card("Growth Rate", pct(demo_stats.get("growth_rate", 0), ".2%"), "green")

            d5, d6, d7, d8 = st.columns(4)
            with d5:
                metric_card("Births", str(demo_stats.get("births", 0)), "green")
            with d6:
                metric_card("Deaths", str(demo_stats.get("deaths", 0)), "red")
            with d7:
                metric_card("Immigrants", str(demo_stats.get("immigrants", 0)), "purple")
            with d8:
                metric_card("Emigrants", str(demo_stats.get("emigrants", 0)), "orange")

        snapshots = api_get("/api/demographics/snapshots?limit=50")
        if snapshots and len(snapshots) > 1:
            section_header("📈", "Population Over Time")
            snap_df = pd.DataFrame(snapshots)
            if "tick" in snap_df.columns:
                snap_df = snap_df.sort_values("tick").set_index("tick")
                st.line_chart(snap_df[["total_population"]], height=200)

        events = api_get("/api/demographics/events?limit=25")
        if events:
            section_header("📜", "Recent Life Events")
            st.dataframe(pd.DataFrame([{
                "Type": e["type"].title(),
                "Description": e["description"],
                "Timestamp": str(e["timestamp"])[:19],
            } for e in events]), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════
# TAB: Infrastructure
# ═══════════════════════════════════════
if "infra" in tabs:
    with tabs["infra"]:
        section_header("📍", "Plan a Build")
        st.caption(
            "Click a spot on the map to preview who it would actually affect before committing "
            "to build. Bridges/roads need two clicks — first point, then the far endpoint."
        )

        PLAN_TYPE_LABELS = {
            "hospital_build": "🏥 Hospital",
            "bridge_build": "🌉 Bridge (2 points)",
            "road_build": "🛣 Road (2 points)",
        }
        plan_type = st.selectbox(
            "What to build", list(PLAN_TYPE_LABELS.keys()),
            format_func=lambda t: PLAN_TYPE_LABELS[t], key="infra_plan_type",
        )
        needs_two_points = plan_type in ("bridge_build", "road_build")

        if "infra_plan_points" not in st.session_state:
            st.session_state.infra_plan_points = []
        if st.session_state.get("infra_plan_type_prev") != plan_type:
            st.session_state.infra_plan_points = []
            st.session_state.infra_plan_last_click = None
            st.session_state.infra_plan_type_prev = plan_type

        plan_districts = api_get("/api/city/districts") or []
        plan_citizens = api_get("/api/citizens/?limit=1200") or []

        if plan_districts:
            fig = go.Figure()

            for d in plan_districts:
                fig.add_shape(
                    type="circle", xref="x", yref="y",
                    x0=d["center_x"] - d["radius"], y0=d["center_y"] - d["radius"],
                    x1=d["center_x"] + d["radius"], y1=d["center_y"] + d["radius"],
                    line=dict(color="rgba(124,108,246,0.35)"),
                    fillcolor="rgba(124,108,246,0.05)",
                )
                fig.add_annotation(
                    x=d["center_x"], y=d["center_y"], text=d["name"], showarrow=False,
                    font=dict(color="#9498ab", size=11),
                )

            cxs = [c["x"] for c in plan_citizens if c.get("x") is not None]
            cys = [c["y"] for c in plan_citizens if c.get("y") is not None]
            if cxs:
                fig.add_trace(go.Scattergl(
                    x=cxs, y=cys, mode="markers",
                    marker=dict(size=3, color="rgba(45,212,167,0.35)"),
                    hoverinfo="skip", showlegend=False,
                ))

            # Plotly's click-select only fires on an actual marker, not blank canvas — lay
            # down a fine, near-invisible grid the user is effectively clicking "through" so
            # any spot on the map is selectable, snapped to the nearest grid point.
            xs = [d["center_x"] for d in plan_districts]
            ys = [d["center_y"] for d in plan_districts]
            rs = [d["radius"] for d in plan_districts]
            min_x, max_x = min(x - r for x, r in zip(xs, rs)) - 100, max(x + r for x, r in zip(xs, rs)) + 100
            min_y, max_y = min(y - r for y, r in zip(ys, rs)) - 100, max(y + r for y, r in zip(ys, rs)) + 100
            step = 150
            grid_x, grid_y = [], []
            gx = min_x
            while gx <= max_x:
                gy = min_y
                while gy <= max_y:
                    grid_x.append(gx)
                    grid_y.append(gy)
                    gy += step
                gx += step

            # Plain Scatter (SVG), not Scattergl (WebGL) — WebGL's picking buffer can drop
            # near-zero-opacity points from hit-testing, which silently breaks click-to-select.
            # hoverinfo="none" (not "skip") — "skip" excludes a trace from hit-testing
            # entirely, which kills click-to-select along with the tooltip; "none" only
            # suppresses the tooltip text and leaves the trace clickable.
            fig.add_trace(go.Scatter(
                x=grid_x, y=grid_y, mode="markers",
                marker=dict(size=14, color="rgba(255,255,255,0)"),
                hoverinfo="none", showlegend=False,
            ))

            if st.session_state.infra_plan_points:
                fig.add_trace(go.Scatter(
                    x=[p[0] for p in st.session_state.infra_plan_points],
                    y=[p[1] for p in st.session_state.infra_plan_points],
                    mode="markers+text",
                    marker=dict(size=16, color="#e8b94d", symbol="star"),
                    text=["A", "B"][:len(st.session_state.infra_plan_points)],
                    textposition="top center", showlegend=False,
                ))

            fig.update_layout(
                height=460, plot_bgcolor="#0a0b10", paper_bgcolor="#0a0b10",
                font=dict(color="#eceef5"),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x"),
                clickmode="event+select",
                dragmode=False,
                hovermode="closest",
            )

            click = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="infra_map_click")
            points = (click.get("selection", {}) or {}).get("points", []) if click else []

            if points:
                new_point = (points[0]["x"], points[0]["y"])
                if st.session_state.get("infra_plan_last_click") != new_point:
                    st.session_state.infra_plan_last_click = new_point
                    if len(st.session_state.infra_plan_points) < (2 if needs_two_points else 1):
                        st.session_state.infra_plan_points.append(new_point)
                        st.rerun()

            if st.button("Clear selection", key="infra_plan_clear"):
                st.session_state.infra_plan_points = []
                st.session_state.infra_plan_last_click = None
                st.rerun()

            ready = len(st.session_state.infra_plan_points) == (2 if needs_two_points else 1)

            if ready:
                x, y = st.session_state.infra_plan_points[0]
                payload = {"project_type": plan_type, "x": x, "y": y}
                if needs_two_points:
                    target_x, target_y = st.session_state.infra_plan_points[1]
                    payload["target_x"] = target_x
                    payload["target_y"] = target_y

                impact = api_post("/api/infrastructure/preview-impact", payload)
                if impact:
                    st.markdown(f"**{impact.get('summary', '')}**")
                    bcol, ccol = st.columns(2)
                    with bcol:
                        st.caption(f"Beneficiaries ({impact.get('total_beneficiaries', 0)} total)")
                        if impact.get("beneficiaries"):
                            st.dataframe(pd.DataFrame(impact["beneficiaries"]), use_container_width=True, hide_index=True)
                    with ccol:
                        st.caption(f"Nearby businesses ({len(impact.get('businesses', []))})")
                        if impact.get("businesses"):
                            st.dataframe(pd.DataFrame(impact["businesses"]), use_container_width=True, hide_index=True)

                    if st.button("🚀 Approve & Start Construction", key="infra_plan_confirm", use_container_width=True):
                        r = api_post("/api/infrastructure/trigger", payload)
                        if r:
                            st.toast(f"Started: {r.get('name')}", icon="🏗")
                            st.session_state.infra_plan_points = []
                            st.session_state.infra_plan_last_click = None
                            st.rerun()
            elif needs_two_points and len(st.session_state.infra_plan_points) == 1:
                st.info("Click a second point to set the endpoint.")
            else:
                st.info("Click a point on the map above to preview its impact.")

        st.markdown("---")

        infra_stats = api_get("/api/infrastructure/stats")
        if infra_stats:
            section_header("⚡", "Infrastructure & Utilities")
            i1, i2, i3, i4, i5, i6 = st.columns(6)
            with i1:
                metric_card("Total Grids", str(infra_stats.get("total_grids", 0)), "blue")
            with i2:
                metric_card("Operational", str(infra_stats.get("operational_grids", 0)), "green")
            with i3:
                metric_card("Avg Health", pct(infra_stats.get("avg_health", 0)), "teal")
            with i4:
                metric_card("Avg Reliability", pct(infra_stats.get("avg_reliability", 0)), "purple")
            with i5:
                metric_card("Active Projects", str(infra_stats.get("active_projects", 0)), "orange")
            with i6:
                metric_card("Completed", str(infra_stats.get("completed_projects", 0)), "green")

        grids = api_get("/api/infrastructure/grids")
        if grids:
            section_header("🔌", "Utility Grids")
            st.dataframe(pd.DataFrame([{
                "Type": g["utility_type"].title(),
                "Load": pct(g["load_pct"]),
                "Reliability": round(g["reliability"], 2),
                "Coverage": round(g["coverage_pct"], 2),
                "Health": round(g["health"], 2),
                "Operational": "Yes" if g["is_operational"] else "No",
                "Price/Unit": g["price_per_unit"],
            } for g in grids]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Reliability": st.column_config.ProgressColumn("Reliability", min_value=0, max_value=1, format="%.0f%%"),
                    "Coverage": st.column_config.ProgressColumn("Coverage", min_value=0, max_value=1, format="%.0f%%"),
                    "Health": st.column_config.ProgressColumn("Health", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

        projects = api_get("/api/infrastructure/projects")
        if projects:
            section_header("🚧", "Infrastructure Projects")
            st.dataframe(pd.DataFrame([{
                "Name": p["name"],
                "Type": p["type"].replace("_", " ").title(),
                "Budget": round(p["budget"]),
                "Spent": round(p["spent"]),
                "Progress": round(p["progress"], 2),
                "Status": "Active" if p["is_active"] else ("Completed" if p["is_completed"] else "Inactive"),
            } for p in projects]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Budget": st.column_config.NumberColumn("Budget", format="$%.0f"),
                    "Spent": st.column_config.NumberColumn("Spent", format="$%.0f"),
                    "Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

# ═══════════════════════════════════════
# TAB: Tourism
# ═══════════════════════════════════════
if "tourism" in tabs:
    with tabs["tourism"]:
        tourism_stats = api_get("/api/tourism/stats")
        if tourism_stats:
            section_header("✈️", "Tourism Overview")
            t1, t2, t3, t4 = st.columns(4)
            with t1:
                metric_card("Hotels", str(tourism_stats.get("total_hotels", 0)), "blue")
            with t2:
                metric_card("Occupancy", pct(tourism_stats.get("occupancy_rate", 0)), "green")
            with t3:
                metric_card("Active Tourists", str(tourism_stats.get("active_tourists", 0)), "purple")
            with t4:
                metric_card("Daily Revenue", dollar(tourism_stats.get("daily_revenue", 0)), "teal")

            t5, t6 = st.columns(2)
            with t5:
                metric_card("Attractions", str(tourism_stats.get("total_attractions", 0)), "orange")
            with t6:
                metric_card("Total Guests Served", str(tourism_stats.get("total_guests_served", 0)), "blue")

        hotels = api_get("/api/tourism/hotels")
        if hotels:
            section_header("🏨", "Hotels")
            st.dataframe(pd.DataFrame([{
                "Name": h["name"],
                "Class": "⭐" * h["class"],
                "Rooms": f"{h['occupied_rooms']}/{h['total_rooms']}",
                "Occupancy": round(h["occupancy_pct"], 2),
                "Price/Night": h["price_per_night"],
                "Rating": round(h["rating"], 1),
                "Revenue": round(h["daily_revenue"]),
            } for h in hotels]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Occupancy": st.column_config.ProgressColumn("Occupancy", min_value=0, max_value=1, format="%.0f%%"),
                    "Price/Night": st.column_config.NumberColumn("Price/Night", format="$%.0f"),
                    "Revenue": st.column_config.NumberColumn("Revenue", format="$%.0f"),
                },
            )

        attractions = api_get("/api/tourism/attractions")
        if attractions:
            section_header("🗽", "Attractions")
            st.dataframe(pd.DataFrame([{
                "Name": a["name"],
                "Type": a["type"].replace("_", " ").title(),
                "Popularity": round(a["popularity"], 2),
                "Ticket": a["ticket_price"],
                "Daily Visitors": a["daily_visitors"],
                "Total Visitors": a["total_visitors"],
                "Rating": round(a["rating"], 1),
            } for a in attractions]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Popularity": st.column_config.ProgressColumn("Popularity", min_value=0, max_value=1, format="%.0f%%"),
                    "Ticket": st.column_config.NumberColumn("Ticket", format="$%.2f"),
                },
            )

        visitors = api_get("/api/tourism/visitors?limit=20")
        if visitors:
            section_header("🧳", "Active Visitors")
            st.dataframe(pd.DataFrame([{
                "Origin": v["origin"],
                "Budget": round(v["budget"]),
                "Spent": round(v["spent"]),
                "Satisfaction": round(v["satisfaction"], 2),
                "Ticks Left": v["ticks_remaining"],
            } for v in visitors]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Budget": st.column_config.NumberColumn("Budget", format="$%.0f"),
                    "Spent": st.column_config.NumberColumn("Spent", format="$%.0f"),
                    "Satisfaction": st.column_config.ProgressColumn("Satisfaction", min_value=0, max_value=1, format="%.0f%%"),
                },
            )

# ══════════════════════════════════════════════════════════════════════
# Auto-refresh — deliberately outside every tab's if-block: this must keep
# running regardless of which tabs the org's plan includes.
# ══════════════════════════════════════════════════════════════════════
if auto_refresh:
    time.sleep(5)
    st.rerun()
