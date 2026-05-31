"""
Medico.AI frontend.

This keeps the project frontend as Streamlit/Python while rendering the provided
HTML design directly for a closer visual match.
"""
from __future__ import annotations

import os
from textwrap import dedent

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="Medico.AI - Save on Medicines",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = os.getenv("MEDICO_API_URL", "http://localhost:8000/api/v1")
HEALTH_URL = os.getenv("MEDICO_HEALTH_URL", "http://localhost:8000/health")

st.markdown(
    """
<style>
html, body, .stApp {
  margin: 0 !important;
  padding: 0 !important;
  background: #F8FAFC !important;
}
.block-container {
  max-width: none !important;
  padding: 0 !important;
}
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="collapsedControl"],
#MainMenu,
footer {
  display: none !important;
}
iframe {
  display: block;
}
</style>
""",
    unsafe_allow_html=True,
)

html_app = dedent(
    f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medico.AI — Save on Medicines</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
      :root {{
        --green: #10B981;
        --green-light: #ecfdf5;
        --green-dark: #047857;
        --orange: #F97316;
        --blue: #3B82F6;
        --bg: #F8FAFC;
        --card: #ffffff;
        --text: #0F172A;
        --muted: #64748B;
        --border: #E2E8F0;
        --shadow: 0 10px 30px -10px rgba(0,0,0,0.06);
        --radius: 16px;
      }}

      * {{ margin: 0; padding: 0; box-sizing: border-box; }}

      body {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: var(--bg);
        color: var(--text);
        min-height: 100vh;
      }}

      nav {{
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
        padding: 0 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 72px;
        position: sticky;
        top: 0;
        z-index: 100;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
      }}
      .logo {{
        display: flex;
        align-items: center;
        gap: 12px;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.6rem;
        color: var(--text);
        text-decoration: none;
      }}
      .logo-icon {{
        width: 42px; height: 42px;
        background: linear-gradient(135deg, #10B981, #059669);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 8px 16px -4px rgba(16,185,129,0.3);
      }}
      .nav-links {{ display: flex; gap: 6px; align-items: center; }}
      .nav-links a {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 600;
        font-size: 0.92rem;
        color: var(--muted);
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 10px;
        transition: all 0.2s ease;
      }}
      .nav-links a:hover, .nav-links a.active {{
        background: var(--green-light);
        color: var(--green-dark);
      }}
      
      .right-nav-container {{
        display: flex;
        align-items: center;
        gap: 16px;
      }}
      
      .status-pill {{
        display: flex; align-items: center; gap: 6px;
        background: var(--green-light);
        color: var(--green-dark);
        font-weight: 700;
        font-size: 0.8rem;
        padding: 6px 14px;
        border-radius: 99px;
        border: 1px solid rgba(16,185,129,0.2);
      }}
      .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }}
      @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}
      
      .auth-actions {{ display:flex; gap:10px; align-items:center; }}
      .auth-btn {{
        border: 1.5px solid var(--border);
        background: white;
        color: var(--text);
        padding: 8px 16px;
        border-radius: 10px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 0.88rem;
        cursor: pointer;
        transition: all 0.2s ease;
      }}
      .auth-btn:hover {{
        border-color: var(--text);
        background: #F8FAFC;
      }}
      .auth-btn.primary {{
        background: var(--text);
        color: white;
        border-color: var(--text);
      }}
      .auth-btn.primary:hover {{
        background: #1E293B;
        border-color: #1E293B;
      }}
      .auth-user {{
        color: var(--text);
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.9rem;
      }}

      /* Glassmorphic Modal */
      .modal {{
        position: fixed; inset: 0; z-index: 999;
        display: none; place-items: center;
        background: rgba(15,23,42,0.4);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        padding: 20px;
        opacity: 0;
        transition: opacity 0.25s ease;
      }}
      .modal.active {{ display: grid; opacity: 1; }}
      .auth-card {{
        width: min(420px, 100%);
        background: white;
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.15);
        border: 1px solid var(--border);
        transform: translateY(20px);
        transition: transform 0.25s ease;
      }}
      .modal.active .auth-card {{ transform: translateY(0); }}
      .auth-card h2 {{
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.6rem;
        margin-bottom: 8px;
        color: var(--text);
      }}
      .auth-card label {{
        font-weight: 600;
        font-size: 0.82rem;
        color: var(--muted);
        display: block;
        margin-top: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }}
      .auth-card input {{
        width: 100%;
        border: 1.5px solid var(--border);
        border-radius: 12px;
        padding: 12px 16px;
        margin-top: 6px;
        font: inherit;
        outline: none;
        transition: all 0.2s ease;
        color: var(--text);
      }}
      .auth-card input:focus {{
        border-color: var(--green);
        box-shadow: 0 0 0 3px rgba(16,185,129,0.15);
      }}
      
      .hero {{
        background: radial-gradient(circle at top left, #065f46 0%, #047857 50%, #065f46 100%);
        padding: 72px 32px 64px;
        text-align: center;
        position: relative;
        overflow: hidden;
      }}
      .hero::before {{
        content: '';
        position: absolute; inset: 0;
        background: url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Ccircle cx='40' cy='40' r='5'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
      }}
      .hero h1 {{
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: clamp(2.2rem, 5vw, 3.2rem);
        color: white;
        line-height: 1.15;
        letter-spacing: -0.02em;
        position: relative;
      }}
      .hero p {{
        color: rgba(255,255,255,0.85);
        font-size: 1.2rem;
        margin: 14px auto 0;
        max-width: 580px;
        font-weight: 500;
        position: relative;
      }}

      .search-section {{
        max-width: 720px;
        margin: -32px auto 0;
        padding: 0 24px;
        position: relative;
        z-index: 10;
      }}
      .search-box {{
        background: white;
        border-radius: 24px;
        padding: 10px 10px 10px 24px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 20px 40px -15px rgba(15,23,42,0.12);
        border: 1px solid var(--border);
        transition: all 0.2s ease;
      }}
      .search-box:focus-within {{
        border-color: var(--green);
        box-shadow: 0 20px 40px -15px rgba(16,185,129,0.15);
      }}
      .search-box input {{
        flex: 1;
        border: none; outline: none;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--text);
        background: transparent;
      }}
      .search-box input::placeholder {{ color: #94A3B8; font-weight: 500; }}
      .search-btn {{
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 14px 32px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
        box-shadow: 0 4px 12px rgba(16,185,129,0.2);
      }}
      .search-btn:hover {{
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(16,185,129,0.3);
      }}
      .search-hint {{
        text-align: center;
        color: var(--muted);
        font-size: 0.88rem;
        margin-top: 12px;
        font-weight: 500;
      }}

      .main {{ max-width: 1020px; margin: 48px auto 80px; padding: 0 24px; }}
      
      .summary-cards {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-bottom: 40px;
      }}
      @media(max-width:768px){{ .summary-cards {{ grid-template-columns: repeat(2,1fr); }} }}
      @media(max-width:480px){{ .summary-cards {{ grid-template-columns: 1fr; }} }}
      
      .sum-card {{
        background: white;
        border-radius: var(--radius);
        padding: 24px 20px;
        text-align: center;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        transition: all 0.25s ease;
      }}
      .sum-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.05);
      }}
      .sum-card .big {{
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 6px;
      }}
      .sum-card .label {{
        font-size: 0.8rem;
        color: var(--muted);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }}
      .sum-card.green .big {{ color: var(--green-dark); }}
      .sum-card.orange .big {{ color: var(--orange); }}
      .sum-card.blue .big {{ color: var(--blue); }}
      .sum-card.save {{
        background: linear-gradient(135deg, var(--green-light), #d1fae5);
        border-color: rgba(16,185,129,0.3);
      }}
      .sum-card.save .big {{ color: var(--green-dark); }}

      .section-title {{
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.4rem;
        color: var(--text);
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
      }}

      .result-card {{
        background: white;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        overflow: hidden;
        margin-bottom: 32px;
      }}
      .result-header {{
        padding: 22px 28px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1.5px solid var(--border);
        background: #FAFAFB;
      }}
      .medicine-name {{
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.4rem;
        color: var(--text);
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
      }}
      .badge {{
        display: inline-flex; align-items: center; gap: 4px;
        padding: 6px 14px;
        border-radius: 99px;
        font-size: 0.8rem;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
      }}
      .badge-green {{ background: var(--green-light); color: var(--green-dark); border: 1px solid rgba(16,185,129,0.2); }}
      .badge-orange {{ background: #FFF7ED; color: #C2410C; border: 1px solid rgba(249,115,22,0.2); }}
      .badge-muted {{ background: #F1F5F9; color: #475569; border: 1px solid rgba(71,85,105,0.15); }}

      .composition {{
        padding: 14px 28px;
        background: #F0FDF4;
        border-bottom: 1px solid var(--border);
        font-size: 0.92rem;
        color: #065F46;
        font-weight: 600;
      }}
      .composition span {{ font-weight: 800; }}
      .options-wrap {{ padding: 0 28px 12px; overflow-x: auto; }}
      
      table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
      thead tr {{ background: #F8FAFC; border-radius: 8px; }}
      th {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--muted);
        padding: 12px 16px;
        text-align: left;
        white-space: nowrap;
      }}
      td {{
        padding: 16px 16px;
        font-size: 0.95rem;
        color: var(--text);
        border-bottom: 1px solid var(--border);
        vertical-align: middle;
      }}
      tr:last-child td {{ border-bottom: none; }}
      tr:hover td {{ background: #F8FAFC; }}
      .best-row td {{ background: #F0FDF4 !important; }}
      .option-name {{ font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 1.05rem; }}
      
      .star-badge {{
        display: inline-flex; align-items: center; gap: 4px;
        background: #FEF3C7; color: #92400E;
        border: 1px solid rgba(251,191,36,0.3);
        padding: 3px 10px; border-radius: 99px;
        font-size: 0.75rem; font-weight: 700;
        margin-left: 8px;
      }}
      .price {{ font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.1rem; }}
      .price-generic {{ color: var(--green-dark); }}
      .price-branded {{ color: var(--orange); }}
      
      .savings-chip {{
        display: inline-block;
        background: var(--green-light);
        color: var(--green-dark);
        border-radius: 8px;
        padding: 4px 10px;
        font-weight: 800;
        font-size: 0.85rem;
      }}

      .cheapest-banner {{
        margin: 0 28px 24px;
        background: linear-gradient(90deg, #10B981, #059669);
        border-radius: 16px;
        padding: 18px 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        color: white;
        box-shadow: 0 10px 20px -10px rgba(16,185,129,0.3);
      }}
      .cheapest-icon {{
        width: 44px; height: 44px;
        background: rgba(255,255,255,0.2);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem; flex-shrink: 0;
      }}
      .cheapest-text .title {{
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.1rem;
      }}
      .cheapest-text .sub {{
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 3px;
      }}

      .how-section {{ margin: 56px 0; }}
      .steps {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 24px; }}
      @media(max-width:768px){{ .steps {{ grid-template-columns: 1fr; }} }}
      
      .step-card {{
        background: white;
        border-radius: var(--radius);
        padding: 32px 24px;
        text-align: center;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        position: relative;
        transition: transform 0.2s ease;
      }}
      .step-card:hover {{ transform: translateY(-3px); }}
      .step-num {{
        width: 46px; height: 46px;
        border-radius: 50%;
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.3rem;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 16px;
        box-shadow: 0 6px 12px rgba(16,185,129,0.25);
      }}
      .step-icon {{ font-size: 2.2rem; margin-bottom: 8px; }}
      .step-card h3 {{
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.15rem;
        margin-bottom: 8px;
      }}
      .step-card p {{ color: var(--muted); font-size: 0.92rem; line-height: 1.5; font-weight: 500; }}

      .upload-card {{
        background: white;
        border-radius: var(--radius);
        padding: 48px 32px;
        text-align: center;
        box-shadow: var(--shadow);
        border: 2px dashed rgba(148,163,184,0.5);
        margin-bottom: 40px;
        transition: all 0.2s ease;
      }}
      .upload-card:hover {{ border-color: var(--green); background: #FAFDFB; }}
      .upload-icon {{ font-size: 3.5rem; margin-bottom: 16px; }}
      .upload-card h2 {{
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.6rem;
        margin-bottom: 8px;
      }}
      .upload-card p {{ color: var(--muted); margin-bottom: 24px; font-weight: 500; }}
      .btn-upload {{
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        border: none;
        padding: 16px 36px;
        border-radius: 14px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        cursor: pointer;
        box-shadow: 0 6px 20px rgba(16,185,129,0.3);
        transition: all 0.2s ease;
      }}
      .btn-upload:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(16,185,129,0.4);
      }}
      
      .scan-panel {{
        display: grid;
        grid-template-columns: 0.90fr 1.10fr;
        gap: 24px;
        align-items: start;
        margin: 24px 0 32px;
      }}
      .preview-box, .scan-detail-box {{
        background: white;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        overflow: hidden;
      }}
      .preview-box img {{
        width: 100%;
        max-height: 480px;
        object-fit: contain;
        background: #F1F5F9;
        display: block;
      }}
      .preview-empty {{
        padding: 48px 24px;
        color: var(--muted);
        font-weight: 600;
        text-align: center;
      }}
      .scan-detail-box {{ padding: 24px; }}
      .pill-list {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
      .med-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 14px;
        border-radius: 99px;
        background: var(--green-light);
        border: 1px solid rgba(16,185,129,0.25);
        color: var(--green-dark);
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 0.88rem;
      }}
      .scan-lines {{
        margin-top: 16px;
        max-height: 240px;
        overflow-y: auto;
        border-top: 1px solid var(--border);
        padding-top: 8px;
      }}
      .scan-line {{
        padding: 10px 0;
        border-bottom: 1px solid #F1F5F9;
        color: var(--muted);
        font-size: 0.9rem;
      }}
      .scan-line strong {{ color: var(--text); margin-right: 8px; }}

      .disclaimer {{
        background: #FFFBEB;
        border: 1px solid rgba(251,191,36,0.3);
        border-radius: 16px;
        padding: 20px 24px;
        display: flex;
        gap: 14px;
        align-items: flex-start;
        margin-top: 32px;
      }}
      .disclaimer-icon {{ font-size: 1.5rem; flex-shrink: 0; }}
      .disclaimer p {{
        color: #92400E;
        font-size: 0.92rem;
        line-height: 1.55;
        font-weight: 600;
      }}

      .tabs {{ display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }}
      .tab {{
        padding: 12px 24px;
        border-radius: 12px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 0.92rem;
        cursor: pointer;
        border: 1px solid var(--border);
        background: white;
        color: var(--muted);
        transition: all 0.2s ease;
      }}
      .tab:hover {{ border-color: #94A3B8; color: var(--text); }}
      .tab.active {{
        background: var(--text);
        color: white;
        border-color: var(--text);
        box-shadow: 0 4px 12px rgba(15,23,42,0.15);
      }}

      .page-section {{ display: none; }}
      .page-section.active {{ display: block; }}
      .loading, .error-msg {{
        text-align: center;
        padding: 24px;
        color: var(--muted);
        font-weight: 700;
      }}
      .error-msg {{ color: #DC2626; }}
      
      .history-item {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        margin-bottom: 12px;
        border-radius: 14px;
        border: 1.5px solid var(--border);
        background: white;
        cursor: pointer;
        transition: all 0.2s ease;
      }}
      .history-item:hover {{
        border-color: var(--green);
        box-shadow: var(--shadow);
        transform: translateX(4px);
      }}

      footer {{
        background: #0F172A;
        color: rgba(255,255,255,0.6);
        text-align: center;
        padding: 32px 24px;
        font-size: 0.9rem;
        margin-top: 120px;
        border-top: 1px solid #1E293B;
      }}
      footer span {{ color: var(--green); font-weight: 700; }}
      
      @media(max-width:768px) {{
        nav {{ height: auto; padding: 16px 24px; flex-direction: column; align-items: flex-start; gap: 14px; }}
        .right-nav-container {{ width: 100%; justify-content: space-between; }}
        .nav-links {{ flex-wrap: wrap; }}
        .search-box {{ flex-direction: column; align-items: stretch; }}
        .summary-cards {{ grid-template-columns: 1fr; }}
        .scan-panel {{ grid-template-columns: 1fr; }}
      }}
    </style>
    </head>
    <body>

    <nav>
      <a href="#" class="logo" onclick="showPage('home', document.querySelector('.nav-links a'))">
        <div class="logo-icon">💊</div>
        Medico.AI
      </a>
      <div class="nav-links">
        <a href="#" class="active" onclick="showPage('home',this)">🏠 Home</a>
        <a href="#" onclick="showPage('upload',this)">📷 Upload Prescription</a>
        <a href="#" onclick="showPage('search',this)">🔍 Search Medicine</a>
        <a href="#" onclick="showPage('browse',this)">📋 Browse</a>
        <a href="#" id="historyLink" onclick="showPage('history',this)" style="display:none">⏳ History</a>
      </div>
      <div class="right-nav-container">
        <div class="status-pill">
          <div class="dot"></div>
          <span id="statusText">Checking backend...</span>
        </div>
        <div id="authContainer" class="auth-actions">
          <button class="auth-btn" onclick="openAuthModal('login')">Login</button>
          <button class="auth-btn primary" onclick="openAuthModal('signup')">Sign Up</button>
        </div>
      </div>
    </nav>

    <!-- Auth Modal -->
    <div id="authModal" class="modal">
      <div class="auth-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
          <h2 id="modalTitle">Welcome Back</h2>
          <button onclick="closeAuthModal()" style="background:none; border:none; font-size:1.8rem; cursor:pointer; color:var(--muted);">&times;</button>
        </div>
        <div id="authError" class="error-msg" style="display:none; margin-bottom:16px; font-size:0.9rem; text-align:left; padding:0;"></div>
        
        <form id="authForm" onsubmit="handleAuthSubmit(event)">
          <div id="nameFieldGroup" style="display:none;">
            <label for="authName">Full Name</label>
            <input type="text" id="authName" placeholder="John Doe">
          </div>
          <div>
            <label for="authEmail">Email Address</label>
            <input type="email" id="authEmail" required placeholder="john@example.com">
          </div>
          <div>
            <label for="authPassword">Password</label>
            <input type="password" id="authPassword" required placeholder="••••••••" minlength="6">
          </div>
          <button type="submit" class="search-btn" style="width:100%; margin-top:20px; padding:14px;" id="authSubmitBtn">Login</button>
        </form>
        <p style="text-align:center; font-size:0.9rem; color:var(--muted); margin-top:20px; font-weight:600;">
          <span id="modalToggleText">Don't have an account?</span>
          <a href="#" id="modalToggleLink" onclick="toggleAuthMode()" style="color:var(--green-dark); font-weight:700; text-decoration:none; margin-left:4px;">Sign Up</a>
        </p>
      </div>
    </div>

    <div id="page-home" class="page-section active">
      <div class="hero">
        <h1>💊 Find Cheaper Medicines<br>Save Up to 80%</h1>
        <p>Upload your prescription or type any branded medicine to instantly find high-quality generic alternatives</p>
      </div>

      <div class="search-section">
        <div class="search-box">
          <span style="font-size:1.4rem">🔍</span>
          <input type="text" id="searchInput" placeholder="e.g. Augmentin, Crocin, Lipitor..." value="Augmentin">
          <button class="search-btn" onclick="searchHome()">Search →</button>
        </div>
        <p class="search-hint">💡 Try: Crocin · Augmentin · Metformin · Lipitor · Paracetamol</p>
      </div>

      <div class="main">
        <div class="how-section">
          <div class="section-title">✨ How It Works</div>
          <div class="steps">
            <div class="step-card">
              <div class="step-icon">📸</div>
              <div class="step-num">1</div>
              <h3>Upload or Search</h3>
              <p>Take a photo of your prescription or simply type the medicine name</p>
            </div>
            <div class="step-card">
              <div class="step-icon">🧠</div>
              <div class="step-num">2</div>
              <h3>AI Finds Alternatives</h3>
              <p>Our intelligent system matches brands to their generic salt compositions instantly</p>
            </div>
            <div class="step-card">
              <div class="step-icon">💰</div>
              <div class="step-num">3</div>
              <h3>Save Big</h3>
              <p>Compare generic drug alternatives side-by-side with Jan Aushadhi prices</p>
            </div>
          </div>
        </div>

        <div id="resultsSection" style="display:none">
          <div class="section-title">📋 Results for "<span id="searchedName">Augmentin</span>"</div>
          <div id="resultsContent"></div>
        </div>
      </div>
    </div>

    <div id="page-upload" class="page-section">
      <div class="main" style="max-width:760px">
        <div class="section-title" style="margin-top:16px">📷 Upload Your Prescription</div>
        <div class="upload-card">
          <div class="upload-icon">🗒️</div>
          <h2>Take a Photo or Upload</h2>
          <p>Our advanced OCR reads handwritten or printed prescriptions to compare costs</p>
          <input id="prescriptionFile" type="file" accept="image/jpeg,image/png,image/webp,image/bmp,image/tiff" style="display:none">
          <button class="btn-upload" onclick="document.getElementById('prescriptionFile').click()">Choose Prescription Image</button>
          <p style="margin-top:14px;font-size:0.85rem;color:#94A3B8" id="selectedFileName">Supports JPG, PNG, WebP, BMP, TIFF · Max 10MB</p>
          <button class="search-btn" id="runOcrBtn" onclick="uploadPrescription()" style="margin-top:20px; display:none; width:100%; padding:14px;">Analyse Prescription Image →</button>
        </div>
        
        <div id="uploadVercelWarning" class="error" style="display:none; margin-bottom:20px; text-align:left; padding:16px; border-radius:12px;"></div>
        
        <div class="scan-panel">
          <div class="preview-box" id="previewBox">
            <div class="preview-empty">Selected prescription image will appear here</div>
          </div>
          <div class="scan-detail-box" id="scanDetails">
            <div class="section-title" style="margin-bottom:8px">Scan Details</div>
            <p style="color:var(--muted);font-weight:600">Choose an image, then run analysis to see detected medicine names and OCR confidence.</p>
          </div>
        </div>
        <div id="uploadResults"></div>
        <div class="disclaimer">
          <div class="disclaimer-icon">🔒</div>
          <p>Your prescription is processed securely. We only extract medicine names for comparison.</p>
        </div>
      </div>
    </div>

    <div id="page-search" class="page-section">
      <div class="main" style="max-width:760px">
        <div class="section-title" style="margin-top:16px">🔍 Search Medicine</div>
        <div class="search-box" style="margin-bottom:16px">
          <span style="font-size:1.4rem">🔍</span>
          <input id="searchPageInput" type="text" placeholder="Type brand or generic name...">
          <button class="search-btn" onclick="searchStandalone()">Search →</button>
        </div>
        <p class="search-hint" style="text-align:left;margin-bottom:24px">Popular: Crocin · Metformin · Atorvastatin · Pantoprazole · Azithromycin</p>
        <div id="searchPageResults"></div>
        <div class="disclaimer">
          <div class="disclaimer-icon">💡</div>
          <p>You can search by brand name like "Crocin" or generic name like "Paracetamol". Both work.</p>
        </div>
      </div>
    </div>

    <div id="page-browse" class="page-section">
      <div class="main">
        <div class="section-title" style="margin-top:16px">📋 Medicine Database</div>
        <div class="tabs" id="categoryTabs">
          <div class="tab active" onclick="browseMedicines('', this)">All</div>
        </div>
        <div id="browseResults" class="result-card" style="padding:48px;text-align:center;color:var(--muted)">
          <div style="font-size:3rem;margin-bottom:16px">📚</div>
          <strong style="font-size:1.15rem;font-family:'Outfit',sans-serif">Medicine database loading...</strong>
        </div>
      </div>
    </div>

    <div id="page-history" class="page-section">
      <div class="main" style="max-width:800px">
        <div class="section-title" style="margin-top:16px">⏳ Your Scan & Search History</div>
        <p style="color:var(--muted); margin-bottom:24px; font-weight:500;">Click on any past scan or search to view the cheaper generic alternatives again.</p>
        <div id="historyResults" class="result-card" style="padding:48px; text-align:center; color:var(--muted)">
          <div style="font-size:3rem; margin-bottom:16px">⏳</div>
          <strong style="font-size:1.15rem; font-family:'Outfit',sans-serif">Loading history...</strong>
        </div>
      </div>
    </div>

    <footer>
      Made with ❤️ for India &nbsp;|&nbsp; <span>Medico.AI</span> &nbsp;|&nbsp; Always consult your doctor before switching medicines
    </footer>

    <script>
      const API_BASE = "{API_BASE}";
      const HEALTH_URL = "{HEALTH_URL}";

      let currentUser = null;

      function esc(value) {{
        return String(value ?? '').replace(/[&<>"']/g, ch => ({{
          '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        }}[ch]));
      }}

      function rupee(value) {{
        const n = Number(value);
        return Number.isFinite(n) ? `₹${{n.toFixed(2)}}` : 'N/A';
      }}

      function showPage(name, el) {{
        document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
        document.getElementById('page-' + name).classList.add('active');
        document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
        if (el) el.classList.add('active');
        
        if (name === 'browse') loadBrowse();
        if (name === 'history') loadHistory();
      }}

      async function updateStatus() {{
        try {{
          const res = await fetch(HEALTH_URL);
          const data = await res.json();
          document.getElementById('statusText').textContent = data.database === 'connected'
            ? `${{data.medicines_in_db}} Medicines Ready`
            : 'Backend Online';
        }} catch (err) {{
          document.getElementById('statusText').textContent = 'Backend Offline';
          document.querySelector('.status-pill').style.borderColor = '#F97316';
          document.querySelector('.status-pill').style.color = '#C2410C';
          document.querySelector('.status-pill').style.background = '#FFF7ED';
        }}
      }}

      function updateAuthUI() {{
        const stored = localStorage.getItem('medico_user');
        const authContainer = document.getElementById('authContainer');
        const historyLink = document.getElementById('historyLink');
        
        if (stored) {{
          try {{
            currentUser = JSON.parse(stored);
            authContainer.innerHTML = `
              <span class="auth-user" style="margin-right:8px;">👋 Hi, ${{esc(currentUser.name)}}</span>
              <button class="auth-btn" onclick="handleLogout()">Logout</button>
            `;
            historyLink.style.display = 'block';
          }} catch (e) {{
            localStorage.removeItem('medico_user');
            currentUser = null;
            authContainer.innerHTML = `
              <button class="auth-btn" onclick="openAuthModal('login')">Login</button>
              <button class="auth-btn primary" onclick="openAuthModal('signup')">Sign Up</button>
            `;
            historyLink.style.display = 'none';
          }}
        }} else {{
          currentUser = null;
          authContainer.innerHTML = `
            <button class="auth-btn" onclick="openAuthModal('login')">Login</button>
            <button class="auth-btn primary" onclick="openAuthModal('signup')">Sign Up</button>
          `;
          historyLink.style.display = 'none';
          if (document.getElementById('page-history').classList.contains('active')) {{
            showPage('home', document.querySelector('.nav-links a'));
          }}
        }}
      }}

      function handleLogout() {{
        localStorage.removeItem('medico_user');
        currentUser = null;
        updateAuthUI();
        showPage('home', document.querySelector('.nav-links a'));
      }}

      let authMode = 'login';

      function openAuthModal(mode) {{
        authMode = mode;
        const modal = document.getElementById('authModal');
        const title = document.getElementById('modalTitle');
        const btn = document.getElementById('authSubmitBtn');
        const toggleText = document.getElementById('modalToggleText');
        const toggleLink = document.getElementById('modalToggleLink');
        const nameGroup = document.getElementById('nameFieldGroup');
        const errorDiv = document.getElementById('authError');
        
        errorDiv.style.display = 'none';
        document.getElementById('authEmail').value = '';
        document.getElementById('authPassword').value = '';
        document.getElementById('authName').value = '';
        
        if (mode === 'signup') {{
          title.textContent = 'Create Account';
          btn.textContent = 'Sign Up';
          toggleText.textContent = 'Already have an account?';
          toggleLink.textContent = 'Login';
          nameGroup.style.display = 'block';
          document.getElementById('authName').required = true;
        }} else {{
          title.textContent = 'Welcome Back';
          btn.textContent = 'Login';
          toggleText.textContent = "Don't have an account?";
          toggleLink.textContent = 'Sign Up';
          nameGroup.style.display = 'none';
          document.getElementById('authName').required = false;
        }}
        
        modal.classList.add('active');
      }}

      function closeAuthModal() {{
        document.getElementById('authModal').classList.remove('active');
      }}

      function toggleAuthMode() {{
        openAuthModal(authMode === 'login' ? 'signup' : 'login');
      }}

      async function handleAuthSubmit(event) {{
        event.preventDefault();
        const errorDiv = document.getElementById('authError');
        errorDiv.style.display = 'none';
        
        const email = document.getElementById('authEmail').value.trim();
        const password = document.getElementById('authPassword').value;
        const name = document.getElementById('authName').value.trim();
        
        const endpoint = authMode === 'login' ? '/auth/login' : '/auth/signup';
        const payload = authMode === 'login' ? {{ email, password }} : {{ email, password, name }};
        
        try {{
          const res = await fetch(`${{API_BASE}}${{endpoint}}`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(payload)
          }});
          
          const data = await res.json();
          if (!res.ok) {{
            throw new Error(data.detail || 'Authentication failed');
          }}
          
          localStorage.setItem('medico_user', JSON.stringify(data));
          closeAuthModal();
          updateAuthUI();
        }} catch (err) {{
          errorDiv.textContent = err.message;
          errorDiv.style.display = 'block';
        }}
      }}

      function summaryHtml(results) {{
        const found = results.filter(r => r.match_type !== 'none' && !r.error);
        const priced = found.filter(r => (r.alternatives || []).some(a => a.price_available !== false));
        let original = 0;
        let cheapest = 0;
        priced.forEach(r => {{
          const alts = (r.alternatives || []).filter(a => a.price_available !== false);
          if (!alts.length) return;
          cheapest += Number(alts[0].brand_price || 0);
          const matched = alts.find(a => String(a.brand_name).toLowerCase() === String(r.matched_brand || '').toLowerCase());
          original += matched ? Number(matched.brand_price || 0) : Math.max(...alts.map(a => Number(a.brand_price || 0)));
        }});
        const saved = Math.max(0, original - cheapest);
        const pct = original > 0 ? saved / original * 100 : 0;
        return `
          <div class="summary-cards">
            <div class="sum-card blue"><div class="big">${{found.length}}</div><div class="label">Medicine Found</div></div>
            <div class="sum-card orange"><div class="big">₹${{original.toFixed(0)}}</div><div class="label">Branded Price / Strip</div></div>
            <div class="sum-card green"><div class="big">₹${{cheapest.toFixed(0)}}</div><div class="label">Generic Price / Strip</div></div>
            <div class="sum-card save"><div class="big">₹${{saved.toFixed(0)}} 💚</div><div class="label">You Save (${{pct.toFixed(0)}}%!)</div></div>
          </div>`;
      }}

      function badgeFor(match) {{
        if (match.match_type === 'exact') return '<span class="badge badge-green">✅ Exact Match</span>';
        if (match.match_type === 'fuzzy') return `<span class="badge badge-orange">~ Fuzzy (${{match.fuzzy_score || 0}}%)</span>`;
        if (match.match_type === 'salt') return '<span class="badge badge-orange">~ Generic Match</span>';
        if (match.match_type === 'web') return '<span class="badge badge-orange">Web Source</span>';
        return '<span class="badge badge-muted">Matched</span>';
      }}

      function webSourceHtml(alt) {{
        const urls = (alt.source_urls || []).slice(0, 3);
        const links = urls.map((url, i) => `<a href="${{esc(url)}}" target="_blank" rel="noopener" style="color:white;text-decoration:underline">Source ${{i + 1}}</a>`).join(' · ');
        return `
          <div class="cheapest-banner" style="background:linear-gradient(90deg,#3B82F6,#1D4ED8)">
            <div class="cheapest-icon">🌐</div>
            <div class="cheapest-text">
              <div class="title">Web info from ${{esc(alt.source || 'public drug databases')}}</div>
              <div class="sub">Generic: ${{esc(alt.generic_name || 'N/A')}} · Form: ${{esc(alt.form || alt.unit_type || 'N/A')}} · Strength: ${{esc(alt.strength || 'N/A')}}</div>
              <div class="sub">Prices are unavailable from this source. ${{links}}</div>
            </div>
          </div>`;
      }}

      function resultsHtml(results) {{
        const found = results.filter(r => r.match_type !== 'none' && !r.error);
        const notFound = results.filter(r => r.match_type === 'none' || r.error);
        if (!found.length && !notFound.length) return '<div class="error-msg">No medicines found. Try a different search.</div>';

        let html = summaryHtml(results);
        found.forEach(r => {{
          const alts = r.alternatives || [];
          if (r.match_type === 'web') {{
            const alt = alts[0] || {{}};
            html += `
            <div class="result-card">
              <div class="result-header">
                <div class="medicine-name">💊 ${{esc(r.matched_brand || r.query)}} ${{badgeFor(r)}}</div>
              </div>
              <div class="composition">🧪 Composition: <span>${{esc(r.salt_composition || alt.generic_name || '')}}</span></div>
              <div class="options-wrap">
                <table>
                  <thead>
                    <tr><th>Name</th><th>Generic</th><th>Manufacturer / Source</th><th>Form</th><th>Price</th></tr>
                  </thead>
                  <tbody>
                    <tr class="best-row">
                      <td><div class="option-name">${{esc(alt.brand_name || r.matched_brand || r.query)}}</div></td>
                      <td>${{esc(alt.generic_name || '')}}</td>
                      <td>${{esc(alt.manufacturer || alt.source || '')}}</td>
                      <td>${{esc((alt.strength || '') + ' ' + (alt.form || alt.unit_type || ''))}}</td>
                      <td><span class="badge badge-muted">Unavailable</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>
              ${{webSourceHtml(alt)}}
            </div>`;
            return;
          }}
          const rows = alts.map((a, index) => {{
            if (a.price_available === false) {{
              return `
              <tr>
                <td><div class="option-name">${{esc(a.brand_name)}}</div><span class="badge badge-orange">Web Source</span></td>
                <td>${{esc(a.generic_name)}}</td>
                <td>${{esc(a.manufacturer || a.source || '')}}</td>
                <td>${{esc((a.strength || '') + ' ' + (a.form || ''))}}</td>
                <td><span class="badge badge-muted">Unavailable</span></td>
                <td><span class="badge badge-muted">N/A</span></td>
              </tr>`;
            }}
            const best = index === 0 ? '<span class="star-badge">⭐ Best Value</span>' : '';
            const priceClass = index === 0 ? 'price-generic' : 'price-branded';
            const save = Number(a.savings_pct || 0) > 0
              ? `<span class="savings-chip">Save ${{Number(a.savings_pct || 0).toFixed(0)}}% 🎉</span>`
              : '<span class="badge badge-muted">Branded</span>';
            const jan = index === 0 && a.jan_aushadhi_price
              ? '<br><span class="badge badge-orange" style="font-size:0.72rem">Jan Aushadhi</span>'
              : '';
            return `
              <tr class="${{index === 0 ? 'best-row' : ''}}">
                <td><div class="option-name">${{esc(a.brand_name)}}</div>${{best}}${{jan}}</td>
                <td>${{esc(a.generic_name)}}</td>
                <td>${{esc(a.manufacturer)}}</td>
                <td>${{esc((a.strength || '') + ' ' + (a.form || ''))}}</td>
                <td><span class="price ${{priceClass}}">${{rupee(a.brand_price)}}</span></td>
                <td>${{save}}</td>
              </tr>`;
          }}).join('');
          const best = alts[0] || {{}};
          html += `
            <div class="result-card">
              <div class="result-header">
                <div class="medicine-name">💊 ${{esc(r.matched_brand || r.query)}} ${{badgeFor(r)}}</div>
              </div>
              <div class="composition">🧪 Active Ingredient: <span>${{esc(r.salt_composition || '')}}</span></div>
              <div class="options-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Option</th>
                      <th>Generic Salt Name</th>
                      <th>Manufacturer</th>
                      <th>Tablet Form</th>
                      <th>Price / Unit</th>
                      <th>You Save</th>
                    </tr>
                  </thead>
                  <tbody>${{rows}}</tbody>
                </table>
              </div>
              <div class="cheapest-banner">
                <div class="cheapest-icon">🏆</div>
                <div class="cheapest-text">
                  <div class="title">Best Deal: ${{esc(best.brand_name || 'Best option')}} @ ${{rupee(best.brand_price)}} per unit</div>
                  <div class="sub">You save ${{rupee(best.savings_vs_brand)}} (${{Number(best.savings_pct || 0).toFixed(0)}}%) compared to branded medicine.</div>
                </div>
              </div>
            </div>`;
        }});

        if (notFound.length) {{
          html += '<div class="result-card" style="padding:20px"><div class="section-title">❓ Not Identified</div>';
          notFound.forEach(r => html += `<div class="error-msg">${{esc(r.query)}} — ${{esc(r.error || 'No match found')}}</div>`);
          html += '</div>';
        }}

        html += `
          <div class="disclaimer">
            <div class="disclaimer-icon">⚠️</div>
            <p><strong>Important:</strong> Medico.AI is an information tool only. Always consult a registered pharmacist or doctor before switching any medicine. Generic medicines contain the same active ingredient but please verify with your healthcare provider.</p>
          </div>`;
        return html;
      }}

      async function searchMedicine(name, targetId) {{
        const target = document.getElementById(targetId);
        target.innerHTML = '<div class="loading">Searching cheaper alternatives...</div>';
        
        const headers = {{}};
        if (currentUser && currentUser.token) {{
          headers['Authorization'] = `Bearer ${currentUser.token}`;
        }}
        
        try {{
          const res = await fetch(`${{API_BASE}}/medicines/search?name=${{encodeURIComponent(name)}}`, {{
            headers: headers
          }});
          if (!res.ok) throw new Error(await res.text());
          const data = await res.json();
          target.innerHTML = resultsHtml([data]);
        }} catch (err) {{
          target.innerHTML = `<div class="error-msg">Cannot reach backend. Is FastAPI running on port 8000?</div>`;
        }}
      }}

      function searchHome() {{
        const val = document.getElementById('searchInput').value.trim() || 'Augmentin';
        document.getElementById('searchedName').textContent = val;
        document.getElementById('resultsSection').style.display = 'block';
        searchMedicine(val, 'resultsContent');
        document.getElementById('resultsSection').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}

      function searchStandalone() {{
        const val = document.getElementById('searchPageInput').value.trim();
        if (!val) return;
        searchMedicine(val, 'searchPageResults');
      }}

      function medicineDetailsHtml(details) {{
        const meds = details && details.length ? details : [];
        if (!meds.length) {{
          return '<p style="color:var(--muted);font-weight:600">No medicine names detected yet.</p>';
        }}
        return `<div class="pill-list">${{meds.map(m => {{
          const extra = [m.form, m.dosage].filter(Boolean).join(' ');
          return `<span class="med-pill">💊 ${{esc(m.name || m)}}${{extra ? ` <small>${{esc(extra)}}</small>` : ''}}</span>`;
        }}).join('')}}</div>`;
      }}

      function scanDetailsHtml(data) {{
        const lines = (data.ocr_lines || []).slice(0, 12).map(line => `
          <div class="scan-line">
            <strong>${{Number(line.confidence || 0)}}%</strong>
            ${{esc(line.text || '')}}
          </div>
        `).join('');
        const steps = (data.ocr_processing_steps || []).slice(0, 5).map(esc).join(' · ');
        return `
          <div class="section-title" style="margin-bottom:8px">Detected Medicines (${{data.total_medicines_found || 0}})</div>
          ${{medicineDetailsHtml(data.extracted_medicine_details || [])}}
          <div style="margin-top:16px;color:var(--muted);font-weight:700;font-size:0.92rem">
            OCR: ${{esc(data.ocr_engine || 'none')}} · Confidence: ${{Number(data.ocr_confidence || 0)}}%
          </div>
          ${{steps ? `<div style="margin-top:6px;color:var(--muted);font-size:0.82rem">Passes: ${{steps}}</div>` : ''}}
          ${{lines ? `<div class="scan-lines">${{lines}}</div>` : ''}}
        `;
      }}

      async function uploadPrescription() {{
        const fileInput = document.getElementById('prescriptionFile');
        const target = document.getElementById('uploadResults');
        if (!fileInput.files.length) {{
          target.innerHTML = '<div class="error-msg">Please choose a prescription image first.</div>';
          return;
        }}
        
        const form = new FormData();
        form.append('file', fileInput.files[0]);
        form.append('ocr_engine', 'auto');
        target.innerHTML = '<div class="loading">Running OCR and AI analysis...</div>';
        
        const headers = {{}};
        if (currentUser && currentUser.token) {{
          headers['Authorization'] = `Bearer ${currentUser.token}`;
        }}
        
        try {{
          try {{
            await fetch(HEALTH_URL, {{ cache: 'no-store' }});
          }} catch (healthErr) {{
            throw new Error('Backend is not reachable. Start FastAPI on port 8000 and try again.');
          }}
          
          const res = await fetch(`${{API_BASE}}/upload`, {{ 
            method: 'POST', 
            body: form,
            headers: headers
          }});
          
          if (!res.ok) {{
            let message = await res.text();
            try {{
              const parsed = JSON.parse(message);
              message = parsed.detail || message;
            }} catch (parseErr) {{}}
            throw new Error(message);
          }}
          const data = await res.json();
          document.getElementById('scanDetails').innerHTML = scanDetailsHtml(data);
          target.innerHTML = `
            <div class="result-card" style="padding:24px">
              <div class="section-title">📄 Raw OCR Text</div>
              <pre style="white-space:pre-wrap;color:var(--muted);font-family:'Plus Jakarta Sans',sans-serif;line-height:1.5">${{esc(data.raw_text || '(empty)')}}</pre>
            </div>
          ` + resultsHtml(data.results || []);
        }} catch (err) {{
          target.innerHTML = `<div class="error-msg">Upload failed: ${{esc(err.message || 'Cannot reach backend. Please refresh and try again.')}}</div>`;
        }}
      }}

      async function loadHistory() {{
        const target = document.getElementById('historyResults');
        if (!currentUser || !currentUser.token) {{
          target.innerHTML = '<div class="error-msg">Please log in to view your history.</div>';
          return;
        }}
        target.innerHTML = '<div class="loading">Loading your search history...</div>';
        try {{
          const res = await fetch(`${{API_BASE}}/auth/history`, {{
            headers: {{ 'Authorization': `Bearer ${currentUser.token}` }}
          }});
          if (!res.ok) throw new Error('Failed to fetch history');
          const data = await res.json();
          
          if (!data || !data.length) {{
            target.innerHTML = `
              <div style="padding:40px; text-align:center;">
                <div style="font-size:3rem; margin-bottom:16px;">🔍</div>
                <h3>No scan or search history found</h3>
                <p style="color:var(--muted); margin-top:8px;">Search for medicines or upload prescriptions to see them here.</p>
              </div>
            `;
            return;
          }
          
          const itemsHtml = data.map(h => {{
            const date = new Date(h.timestamp).toLocaleString();
            return `
              <div class="history-item" onclick="viewHistoryItem('${{esc(h.medicines_searched)}}')">
                <div style="display:flex; flex-direction:column; align-items:flex-start; gap:4px;">
                  <div style="font-weight:800; font-family:'Outfit',sans-serif; color:var(--text); font-size:1.1rem;">💊 ${{esc(h.medicines_searched)}}</div>
                  <div style="font-size:0.85rem; color:var(--muted);">${{esc(date)}}</div>
                </div>
                <div style="font-weight:700; color:var(--green-dark); font-size:0.9rem;">View Alternatives →</div>
              </div>
            `;
          }}).join('');
          
          target.className = '';
          target.style.padding = '0';
          target.innerHTML = itemsHtml;
        }} catch (err) {{
          target.className = 'result-card';
          target.style.padding = '24px';
          target.innerHTML = `<div class="error-msg">${{esc(err.message)}}</div>`;
        }}
      }}

      function viewHistoryItem(meds) {{
        // Redirect to standalone search page and search
        showPage('search', document.querySelector('.nav-links a[onclick*="search"]'));
        document.getElementById('searchPageInput').value = meds;
        searchStandalone();
      }}

      async function loadCategories() {{
        try {{
          const res = await fetch(`${{API_BASE}}/categories`);
          const cats = await res.json();
          const wrap = document.getElementById('categoryTabs');
          cats.slice(0, 8).forEach(cat => {{
            const div = document.createElement('div');
            div.className = 'tab';
            div.textContent = cat;
            div.onclick = () => browseMedicines(cat, div);
            wrap.appendChild(div);
          }});
        }} catch (err) {{}}
      }}

      async function loadBrowse() {{
        const target = document.getElementById('browseResults');
        if (target.dataset.loaded) return;
        browseMedicines('', document.querySelector('#categoryTabs .tab'));
      }}

      async function browseMedicines(category, el) {{
        document.querySelectorAll('#categoryTabs .tab').forEach(t => t.classList.remove('active'));
        if (el) el.classList.add('active');
        const target = document.getElementById('browseResults');
        target.dataset.loaded = '1';
        target.innerHTML = '<div class="loading">Loading medicines...</div>';
        try {{
          const params = new URLSearchParams({{ limit: 80 }});
          if (category) params.set('category', category);
          const res = await fetch(`${{API_BASE}}/medicines?${{params}}`);
          const meds = await res.json();
          const rows = meds.map(m => {{
            const savings = Number(m.brand_price_per_unit || 0) - Number(m.generic_price_per_unit || 0);
            const pct = Number(m.brand_price_per_unit || 0) > 0 ? savings / Number(m.brand_price_per_unit) * 100 : 0;
            return `
              <tr>
                <td><div class="option-name">${{esc(m.brand_name)}}</div></td>
                <td>${{esc(m.generic_name)}}</td>
                <td>${{esc(m.salt_composition)}}</td>
                <td>${{esc(m.category)}}</td>
                <td><span class="price price-branded">${{rupee(m.brand_price_per_unit)}}</span></td>
                <td><span class="price price-generic">${{rupee(m.generic_price_per_unit)}}</span></td>
                <td><span class="savings-chip">${{pct.toFixed(0)}}%</span></td>
              </tr>`;
          }}).join('');
          target.className = 'result-card';
          target.style.padding = '0';
          target.innerHTML = `
            <div class="options-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Brand</th><th>Generic</th><th>Salt</th><th>Category</th>
                    <th>Brand Price</th><th>Generic Price</th><th>Savings</th>
                  </tr>
                </thead>
                <tbody>${{rows}}</tbody>
              </table>
            </div>`;
        }} catch (err) {{
          target.innerHTML = '<div class="error-msg">Cannot load medicine database.</div>';
        }}
      }}

      document.getElementById('searchInput').addEventListener('keydown', e => {{
        if (e.key === 'Enter') searchHome();
      }});
      document.getElementById('searchPageInput').addEventListener('keydown', e => {{
        if (e.key === 'Enter') searchStandalone();
      }});
      
      document.getElementById('prescriptionFile').addEventListener('change', e => {{
        const file = e.target.files && e.target.files[0];
        const preview = document.getElementById('previewBox');
        const details = document.getElementById('scanDetails');
        const runBtn = document.getElementById('runOcrBtn');
        const nameP = document.getElementById('selectedFileName');
        
        if (!file) {{
          preview.innerHTML = '<div class="preview-empty">Selected prescription image will appear here</div>';
          runBtn.style.display = 'none';
          nameP.textContent = 'Supports JPG, PNG, WebP, BMP, TIFF · Max 10MB';
          return;
        }}
        
        nameP.textContent = `${{esc(file.name)}} · ${(file.size / 1024).toFixed(1)} KB`;
        runBtn.style.display = 'block';
        
        const url = URL.createObjectURL(file);
        preview.innerHTML = `<img src="${{url}}" alt="Selected prescription image">`;
        details.innerHTML = `
          <div class="section-title" style="margin-bottom:8px">Ready to Scan</div>
          <p style="color:var(--muted);font-weight:700">${{esc(file.name)}}</p>
          <p style="color:var(--muted);font-weight:600;margin-top:8px">Click the button above to extract medicine names from this image using Gemini OCR.</p>
        `;
      }});

      // Close modal on click outside
      window.addEventListener('click', e => {{
        const modal = document.getElementById('authModal');
        if (e.target === modal) {{
          closeAuthModal();
        }}
      }});

      // Vercel check: show warning if GEMINI_API_KEY is not set in Vercel environment
      function checkVercelEnvironment() {{
        const isVercel = window.location.hostname.includes('vercel.app');
        if (isVercel) {{
          const warningDiv = document.getElementById('uploadVercelWarning');
          fetch(HEALTH_URL)
            .then(res => res.json())
            .then(data => {{
              warningDiv.innerHTML = `💡 <strong>Vercel Deployment Tip:</strong> Ensure you have configured <code>GEMINI_API_KEY</code> in your Vercel Environment Variables dashboard for prescription scans to work perfectly in the cloud.`;
              warningDiv.style.display = 'block';
              warningDiv.style.background = '#EFF6FF';
              warningDiv.style.color = '#1E40AF';
              warningDiv.style.border = '1px solid rgba(59,130,246,0.3)';
            }}).catch(() => {{}});
        }}
      }}

      updateStatus();
      updateAuthUI();
      loadCategories();
      checkVercelEnvironment();
    </script>
    </body>
    </html>
    """
)

components.html(html_app, height=1500, scrolling=True)
