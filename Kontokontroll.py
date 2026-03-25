"""
Bokföringskontroll — automatisk kvalitetsgranskning av transaktionsdata.
Kör lokalt med: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import altair as alt
import io
import calendar

st.set_page_config(
    page_title="Kontokontroll",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Färgpalett ---
COLORS = {
    "primary": "#1e3a5f",
    "primary_light": "#2d5f8a",
    "hog": "#c53030",
    "hog_bg": "#fff5f5",
    "hog_border": "#fed7d7",
    "medium": "#b7791f",
    "medium_bg": "#fffff0",
    "medium_border": "#fefcbf",
    "lag": "#276749",
    "lag_bg": "#f0fff4",
    "lag_border": "#c6f6d5",
    "text": "#1a202c",
    "text_muted": "#718096",
    "bg_subtle": "#f7fafc",
    "border": "#e2e8f0",
}

TYP_COLORS = {
    "Obalans": "#c53030",
    "Momsfel": "#e53e3e",
    "Löneskatt": "#9b2c2c",
    "Möjlig dubblett": "#dd6b20",
    "Semesterlön": "#c05621",
    "AG-avg semester": "#b7791f",
    "Periodisering": "#b7791f",
    "Ovanlig kombination": "#38a169",
}

TYP_IKONER = {
    "Obalans": "⚖️",
    "Momsfel": "🧾",
    "Löneskatt": "💰",
    "Möjlig dubblett": "👯",
    "Semesterlön": "🏖️",
    "AG-avg semester": "🏖️",
    "Periodisering": "📅",
    "Ovanlig kombination": "🔍",
}

ALLV_ORDER = ["Hög", "Medium", "Låg"]
ALLV_COLORS = [COLORS["hog"], "#dd6b20", "#38a169"]

# --- Custom CSS ---
st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    html, body, [class*="st-"] {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        color: {COLORS["text"]};
    }}

    /* Header */
    .app-header {{
        background: linear-gradient(135deg, #1a3a2d 0%, #276749 50%, #38a169 100%);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        margin-bottom: 1.4rem;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(26, 58, 45, 0.15);
        position: relative;
        overflow: hidden;
    }}
    .app-header::before {{
        content: '';
        position: absolute;
        top: -40%; right: -10%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }}
    .app-header::after {{
        content: '';
        position: absolute;
        bottom: -50%; left: 10%;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
        border-radius: 50%;
    }}
    .app-header-left {{
        position: relative; z-index: 1;
    }}
    .app-header-left h1 {{
        margin: 0; font-size: 1.6rem; font-weight: 700;
        letter-spacing: -0.01em;
    }}
    .app-header-left p {{
        margin: 0.3rem 0 0 0; opacity: 0.75; font-size: 0.88rem;
        font-weight: 400;
    }}
    .app-header .badge {{
        position: relative; z-index: 1;
        background: rgba(255,255,255,0.12);
        backdrop-filter: blur(4px);
        padding: 0.3rem 0.9rem; border-radius: 20px;
        font-size: 0.68rem; letter-spacing: 0.05em;
        font-weight: 500;
        border: 1px solid rgba(255,255,255,0.15);
    }}

    /* Stat-bar */
    .stat-bar {{
        display: flex; gap: 1.5rem; padding: 0.7rem 1rem;
        background: {COLORS["bg_subtle"]};
        border-radius: 14px; margin-bottom: 1rem;
    }}
    .stat-bar .stat {{
        font-size: 0.82rem; color: {COLORS["text_muted"]};
    }}
    .stat-bar .stat strong {{
        color: {COLORS["text"]}; font-weight: 600;
    }}

    /* Metric-kort */
    .metrics-row {{
        display: flex; gap: 0.75rem; margin-bottom: 1.2rem;
    }}
    .metric-card {{
        flex: 1; border-radius: 16px; padding: 1.1rem;
        text-align: center; border: 1px solid {COLORS["border"]};
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(0,0,0,0.07);
    }}
    .metric-card .label {{
        font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 0.2rem;
    }}
    .metric-card .value {{
        font-size: 1.8rem; font-weight: 700; line-height: 1.2;
    }}
    .mc-total {{ background: {COLORS["bg_subtle"]}; }}
    .mc-total .label {{ color: {COLORS["text_muted"]}; }}
    .mc-total .value {{ color: {COLORS["primary"]}; }}
    .mc-hog {{ background: {COLORS["hog_bg"]}; border-color: {COLORS["hog_border"]}; }}
    .mc-hog .label, .mc-hog .value {{ color: {COLORS["hog"]}; }}
    .mc-medium {{ background: {COLORS["medium_bg"]}; border-color: {COLORS["medium_border"]}; }}
    .mc-medium .label, .mc-medium .value {{ color: {COLORS["medium"]}; }}
    .mc-lag {{ background: {COLORS["lag_bg"]}; border-color: {COLORS["lag_border"]}; }}
    .mc-lag .label, .mc-lag .value {{ color: {COLORS["lag"]}; }}

    /* Flagglista */
    .flagg-list {{
        display: flex; flex-direction: column; gap: 0;
        border: 1px solid {COLORS["border"]}; border-radius: 16px;
        overflow: hidden; margin-bottom: 1.2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }}
    .flagg-row {{
        display: grid;
        grid-template-columns: 5px 70px 1fr auto;
        align-items: center;
        padding: 0; min-height: 56px;
        border-bottom: 1px solid {COLORS["border"]};
        background: white; font-size: 0.84rem;
        transition: background 0.12s ease;
    }}
    .flagg-row:last-child {{ border-bottom: none; }}
    .flagg-row:hover {{ background: {COLORS["bg_subtle"]}; }}
    .flagg-stripe {{ height: 100%; border-radius: 0; }}
    .flagg-stripe.s-hog {{ background: {COLORS["hog"]}; }}
    .flagg-stripe.s-medium {{ background: #dd6b20; }}
    .flagg-stripe.s-lag {{ background: #38a169; }}
    .flagg-badge {{
        text-align: center; font-size: 0.72rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.04em;
        padding: 0.2rem 0;
    }}
    .flagg-badge.b-hog {{ color: {COLORS["hog"]}; }}
    .flagg-badge.b-medium {{ color: #dd6b20; }}
    .flagg-badge.b-lag {{ color: #38a169; }}
    .flagg-body {{
        padding: 0.65rem 0.9rem;
    }}
    .flagg-body .flagg-desc {{
        color: {COLORS["text"]}; line-height: 1.45;
    }}
    .flagg-body .flagg-meta {{
        margin-top: 0.25rem; font-size: 0.75rem; color: {COLORS["text_muted"]};
        line-height: 1.35;
    }}
    .flagg-ver {{
        padding-right: 1.1rem; font-size: 0.75rem; color: {COLORS["text_muted"]};
        font-family: ui-monospace, 'SF Mono', monospace;
        white-space: nowrap;
    }}
    .flagg-group-header {{
        font-size: 0.82rem; font-weight: 600; color: {COLORS["text"]};
        padding: 0.8rem 0 0.35rem 0;
    }}

    /* Välkomstvy */
    .welcome-box {{
        text-align: center; padding: 3.5rem 2rem;
        background: {COLORS["bg_subtle"]}; border: 2px dashed #cbd5e0;
        border-radius: 10px; margin: 1.5rem 0;
    }}
    .welcome-box .icon {{ font-size: 2.5rem; margin-bottom: 0.8rem; }}
    .welcome-box h2 {{
        color: {COLORS["text"]}; font-size: 1.2rem;
        font-weight: 600; margin-bottom: 0.4rem;
    }}
    .welcome-box p {{
        color: {COLORS["text_muted"]}; font-size: 0.9rem;
        max-width: 440px; margin: 0 auto;
    }}
    .welcome-box .format-hint {{
        background: white; border: 1px solid {COLORS["border"]};
        border-radius: 6px; padding: 0.8rem 1.2rem;
        margin-top: 1.2rem; display: inline-block;
        text-align: left; font-size: 0.8rem; color: {COLORS["text_muted"]};
        font-family: ui-monospace, 'SF Mono', monospace;
    }}

    /* Export */
    .export-bar {{
        background: {COLORS["bg_subtle"]}; border: 1px solid {COLORS["border"]};
        border-radius: 14px; padding: 0.8rem 1.2rem;
        display: flex; align-items: center; justify-content: space-between;
        margin-top: 0.8rem;
    }}
    .export-bar p {{
        margin: 0; font-size: 0.82rem; color: {COLORS["text_muted"]};
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 0.3rem; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0 0; padding: 0.5rem 1.1rem; font-weight: 500;
        font-size: 0.9rem; transition: background 0.12s ease;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{ background: {COLORS["bg_subtle"]}; }}
    section[data-testid="stSidebar"] .stNumberInput label {{ font-size: 0.82rem; }}

    /* Sektion */
    .section-label {{
        font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.06em; color: {COLORS["text_muted"]};
        margin-bottom: 0.5rem;
    }}

    /* Trafikljus */
    .tl-section {{
        margin-bottom: 0.75rem;
    }}
    .tl-header {{
        display: flex; align-items: center; gap: 0.5rem;
        padding: 0.55rem 1rem; border-radius: 14px 14px 0 0;
        font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .tl-header.tl-hog {{ background: {COLORS["hog_bg"]}; color: {COLORS["hog"]}; }}
    .tl-header.tl-medium {{ background: {COLORS["medium_bg"]}; color: {COLORS["medium"]}; }}
    .tl-header.tl-lag {{ background: {COLORS["lag_bg"]}; color: {COLORS["lag"]}; }}
    .tl-dot {{
        width: 10px; height: 10px; border-radius: 50%; display: inline-block;
    }}
    .tl-dot.d-hog {{ background: {COLORS["hog"]}; }}
    .tl-dot.d-medium {{ background: #dd6b20; }}
    .tl-dot.d-lag {{ background: #38a169; }}
    .tl-list {{
        border: 1px solid {COLORS["border"]}; border-top: none;
        border-radius: 0 0 14px 14px; overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .tl-item {{
        display: grid; grid-template-columns: 1fr auto;
        align-items: center; padding: 0.6rem 1rem;
        border-bottom: 1px solid {COLORS["border"]};
        font-size: 0.84rem; background: white;
        transition: background 0.12s ease;
    }}
    .tl-item:last-child {{ border-bottom: none; }}
    .tl-item:hover {{ background: {COLORS["bg_subtle"]}; }}
    .tl-item .tl-desc {{
        color: {COLORS["text"]}; line-height: 1.4;
    }}
    .tl-item .tl-meta {{
        font-size: 0.75rem; color: {COLORS["text_muted"]}; margin-top: 0.2rem;
    }}
    .tl-item .tl-belopp {{
        font-weight: 600; font-size: 0.9rem; white-space: nowrap;
        padding-left: 1rem; text-align: right;
    }}
    .tl-item .tl-belopp.b-hog {{ color: {COLORS["hog"]}; }}
    .tl-item .tl-belopp.b-medium {{ color: {COLORS["medium"]}; }}
    .tl-item .tl-belopp.b-lag {{ color: {COLORS["lag"]}; }}

    /* Succes-box */
    .success-box {{
        text-align: center; padding: 3rem 2rem;
        background: {COLORS["lag_bg"]}; border: 1px solid {COLORS["lag_border"]};
        border-radius: 20px; margin: 1.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .success-box .icon {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
    .success-box h2 {{ color: {COLORS["lag"]}; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.3rem; }}
    .success-box p {{ color: {COLORS["text_muted"]}; font-size: 0.85rem; }}

    /* Globala avrundningar på Streamlit-widgets */
    /* Filuppladdning — centrerad 70% */
    .upload-wrapper {{
        max-width: 70%; margin: 0 auto 1.2rem auto;
    }}
    .stFileUploader > div {{
        border-radius: 16px !important;
    }}
    .stMultiSelect > div > div {{
        border-radius: 12px !important;
    }}
    .stDataFrame {{
        border-radius: 14px !important; overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }}
    button[kind="secondary"], .stDownloadButton > button {{
        border-radius: 12px !important;
    }}

    /* Apple-stil segmented controls i sidebar */
    section[data-testid="stSidebar"] .stRadio > div {{
        display: flex !important;
        background: #e8ecf1;
        border-radius: 22px;
        padding: 3px;
        gap: 2px;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label {{
        flex: 1;
        border-radius: 20px;
        padding: 0.35rem 0;
        font-size: 0.78rem;
        font-weight: 500;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        color: {COLORS["text_muted"]};
        background: transparent;
        margin: 0;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"] > div:first-child {{
        display: none !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {{
        background: #38a169;
        color: white;
        box-shadow: 0 1px 6px rgba(56, 161, 105, 0.3);
        font-weight: 600;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:not(:has(input:checked)):hover {{
        background: rgba(0,0,0,0.04);
    }}
    section[data-testid="stSidebar"] .stRadio p {{
        font-size: 0.78rem !important;
    }}
    /* Kontrollnamn */
    .ctrl-label {{
        font-size: 0.85rem; font-weight: 600; color: {COLORS["text"]};
        margin-bottom: 0.25rem;
    }}

    /* Segmented controls i huvudinnehåll (tabs inom tabs) */
    .stTabs .stTabs [data-baseweb="tab-list"] {{
        background: #e8ecf1;
        border-radius: 22px;
        padding: 3px;
        gap: 2px;
    }}
    .stTabs .stTabs [data-baseweb="tab"] {{
        border-radius: 20px !important;
        padding: 0.4rem 1.2rem;
        font-size: 0.84rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    .stTabs .stTabs [aria-selected="true"] {{
        background: white !important;
        box-shadow: 0 1px 6px rgba(0,0,0,0.1);
        font-weight: 600;
    }}
    .stTabs .stTabs [aria-selected="false"] {{
        background: transparent !important;
    }}
</style>
""", unsafe_allow_html=True)


# --- Header ---
st.markdown("""
<div class="app-header">
    <div class="app-header-left">
        <h1>Kontokontroll</h1>
        <p>Automatisk kvalitetsgranskning av transaktionsdata</p>
    </div>
    <span class="badge">LOKAL HANTERING</span>
</div>
""", unsafe_allow_html=True)


# --- Sidopanel ---
_SP = '<div style="height:0.6rem"></div>'

with st.sidebar:
    st.markdown("### Aktiva kontroller")

    # === MOMSKONTROLL ===
    st.markdown('<div class="ctrl-label">Momskontroll</div>', unsafe_allow_html=True)
    kontroll_moms_aktiv = st.radio("m", ["På", "Av"], horizontal=True, key="t_moms", label_visibility="collapsed") == "På"
    if kontroll_moms_aktiv:
        with st.expander("Inställningar", expanded=False):
            st.caption("Momskonton")
            mc1, mc2 = st.columns(2)
            with mc1:
                moms_utg_25 = st.number_input("Utg. 25%", value=2610, step=1)
                moms_utg_6 = st.number_input("Utg. 6%", value=2630, step=1)
            with mc2:
                moms_utg_12 = st.number_input("Utg. 12%", value=2620, step=1)
                moms_ing = st.number_input("Ingående", value=2640, step=1)
            st.divider()
            st.caption("Försäljningskonto → momssats")
            fc1, fc2 = st.columns(2)
            with fc1:
                forsa_3010_moms = st.selectbox("3010 Varor", ["25%", "12%", "6%"], index=0, key="f3010")
            with fc2:
                forsa_3020_moms = st.selectbox("3020 Tjänster", ["25%", "12%", "6%"], index=0, key="f3020")
    else:
        moms_utg_25, moms_utg_12, moms_utg_6, moms_ing = 2610, 2620, 2630, 2640
        forsa_3010_moms, forsa_3020_moms = "25%", "25%"

    moms_sats_map = {"25%": moms_utg_25, "12%": moms_utg_12, "6%": moms_utg_6}
    forsakonto_moms = {
        3010: moms_sats_map[forsa_3010_moms],
        3020: moms_sats_map[forsa_3020_moms],
    }

    st.markdown(_SP, unsafe_allow_html=True)

    # === PERIODISERING ===
    st.markdown('<div class="ctrl-label">Periodisering</div>', unsafe_allow_html=True)
    kontroll_period_aktiv = st.radio("p", ["På", "Av"], horizontal=True, key="t_period", label_visibility="collapsed") == "På"
    if kontroll_period_aktiv:
        with st.expander("Inställningar", expanded=False):
            st.caption("Tröskelbelopp")
            period_troskel = st.number_input(
                "Belopp (kr)", value=50000, min_value=1000, max_value=1000000, step=5000,
                help="Poster över detta belopp flaggas",
            )
            st.divider()
            st.caption("Vilka kostnadstyper ska kontrolleras?")
            period_hyra = st.checkbox("Hyra (5010-5060)", value=True, key="p_hyra")
            period_forsakring = st.checkbox("Försäkringar (6310-6399)", value=True, key="p_forsakring")
            period_pension = st.checkbox("Pension & löneskatt (7410-7530)", value=True, key="p_pension")
            period_ovriga = st.checkbox("Övriga kostnadskonton (4000-6999)", value=False, key="p_ovriga")
    else:
        period_troskel = 50000
        period_hyra = period_forsakring = period_pension = period_ovriga = False

    period_konto_ranges = []
    if kontroll_period_aktiv:
        if period_hyra:
            period_konto_ranges.append((5010, 5060))
        if period_forsakring:
            period_konto_ranges.append((6310, 6399))
        if period_pension:
            period_konto_ranges.append((7410, 7530))
        if period_ovriga:
            period_konto_ranges.append((4000, 6999))

    st.markdown(_SP, unsafe_allow_html=True)

    # === DUBBLETTER ===
    st.markdown('<div class="ctrl-label">Dubblettdetektering</div>', unsafe_allow_html=True)
    kontroll_dubblett_aktiv = st.radio("d", ["På", "Av"], horizontal=True, key="t_dubblett", label_visibility="collapsed") == "På"
    if kontroll_dubblett_aktiv:
        with st.expander("Inställningar", expanded=False):
            dc1, dc2 = st.columns(2)
            with dc1:
                dubblett_dagar = st.number_input("Max dagar", value=5, min_value=1, max_value=30, step=1)
            with dc2:
                dubblett_tolerans = st.number_input("Tolerans %", value=1.0, min_value=0.0, max_value=10.0, step=0.1)
    else:
        dubblett_dagar, dubblett_tolerans = 5, 1.0

    st.markdown(_SP, unsafe_allow_html=True)

    # === BALANSKONTROLL ===
    st.markdown('<div class="ctrl-label">Balanskontroll</div>', unsafe_allow_html=True)
    kontroll_balans_aktiv = st.radio("b", ["På", "Av"], horizontal=True, key="t_balans", label_visibility="collapsed") == "På"
    if kontroll_balans_aktiv:
        with st.expander("Inställningar", expanded=False):
            balans_tolerans = st.number_input(
                "Tolerans (kr)", value=0.01, min_value=0.0, max_value=1.0, step=0.01
            )
    else:
        balans_tolerans = 0.01

    st.markdown(_SP, unsafe_allow_html=True)

    # === OVANLIGA KOMBINATIONER ===
    st.markdown('<div class="ctrl-label">Ovanliga kombinationer</div>', unsafe_allow_html=True)
    kontroll_kombo_aktiv = st.radio("k", ["På", "Av"], horizontal=True, key="t_kombo", label_visibility="collapsed") == "På"

    # Lönekontroll — defaultvärden (beräkningen sker på lönesidan)
    kontroll_lone_aktiv = False
    cfg_arbg_sats = 0.3142
    cfg_loneskatt_sats = 0.2426
    cfg_semester_sats = 0.12
    cfg_semester_tillagg = 0.008
    cfg_konto_pension = 7410
    cfg_konto_slp = 7530
    cfg_konto_semlon = 7090
    cfg_konto_ag_sem = 7519
    cfg_tolerans_lon = 1.0


# --- Filuppladdning ---
_, upload_col, _ = st.columns([0.15, 0.7, 0.15])
with upload_col:
    uploaded_file = st.file_uploader(
        "Ladda upp transaktionsdata (Excel/CSV)",
        type=["xlsx", "xls", "csv"],
        help="Förväntade kolumner: Verifikationsnr, Datum, Konto, Debet, Kredit",
    )

if uploaded_file is None:
    st.stop()


# --- Läs in filen ---
try:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, sep=";", decimal=",")
        if len(df.columns) <= 1:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=",", decimal=".")
    else:
        df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Kunde inte läsa filen: {e}")
    st.stop()


# --- Kolumnmappning ---
KOLUMN_ALIAS = {
    "Verifikationsnr": ["ver.nr", "vernr", "verifikation", "voucherno", "voucher_no", "ver nr", "verifikat"],
    "Datum": ["date", "bokföringsdatum", "bokfdatum", "transaktionsdatum", "trans_date"],
    "Konto": ["kontonr", "account", "konto nr", "kontonummer", "account_no"],
    "Debet": ["debit", "deb"],
    "Kredit": ["credit", "kred", "cred"],
}

required_cols = ["Verifikationsnr", "Datum", "Konto", "Debet", "Kredit"]
col_mapping = {}
automapped = {}

for req_col in required_cols:
    if req_col in df.columns:
        col_mapping[req_col] = req_col
    else:
        lower_cols = {c.lower().strip(): c for c in df.columns}
        if req_col.lower() in lower_cols:
            col_mapping[req_col] = lower_cols[req_col.lower()]
            automapped[req_col] = col_mapping[req_col]
        else:
            found = False
            for alias in KOLUMN_ALIAS.get(req_col, []):
                if alias.lower() in lower_cols:
                    col_mapping[req_col] = lower_cols[alias.lower()]
                    automapped[req_col] = col_mapping[req_col]
                    found = True
                    break
            if not found:
                col_mapping[req_col] = None

unmapped = [c for c in required_cols if col_mapping[c] is None]

if automapped:
    mapped_text = ", ".join(f"**{orig}** → {target}" for orig, target in automapped.items())
    st.info(f"Automatisk kolumnmappning: {mapped_text}")

if unmapped:
    st.warning(f"Kunde inte matcha kolumnerna: **{', '.join(unmapped)}**. Välj rätt kolumn nedan.")
    file_cols = ["— Välj —"] + list(df.columns)
    map_cols = st.columns(len(unmapped))
    for i, req_col in enumerate(unmapped):
        with map_cols[i]:
            val = st.selectbox(f"{req_col}", options=file_cols, key=f"map_{req_col}")
            if val != "— Välj —":
                col_mapping[req_col] = val

    still_missing = [c for c in required_cols if col_mapping[c] is None]
    if still_missing:
        st.error(f"Mappa alla kolumner för att fortsätta. Saknas: {', '.join(still_missing)}")
        st.stop()

rename_map = {v: k for k, v in col_mapping.items() if v != k and v is not None}
if rename_map:
    df = df.rename(columns=rename_map)

har_text = "Text" in df.columns
har_kontonamn = "Kontonamn" in df.columns

df["Datum"] = pd.to_datetime(df["Datum"])
df["Debet"] = pd.to_numeric(df["Debet"], errors="coerce").fillna(0)
df["Kredit"] = pd.to_numeric(df["Kredit"], errors="coerce").fillna(0)
df["Belopp"] = df["Debet"] - df["Kredit"]

period_start = df["Datum"].min().strftime("%Y-%m-%d")
period_slut = df["Datum"].max().strftime("%Y-%m-%d")

st.markdown(f"""
<div class="stat-bar">
    <span class="stat"><strong>{len(df)}</strong> rader</span>
    <span class="stat"><strong>{df['Verifikationsnr'].nunique()}</strong> verifikationer</span>
    <span class="stat">Period: <strong>{period_start}</strong> — <strong>{period_slut}</strong></span>
</div>
""", unsafe_allow_html=True)


# =====================================================
# KONTROLLER
# =====================================================

alla_flaggor = []


def _flagga(rad, typ, allvarlighet, ver_nr, beskrivning):
    f = {
        "Typ": typ,
        "Allvarlighet": allvarlighet,
        "Verifikationsnr": ver_nr,
        "Datum": rad["Datum"],
        "Konto": rad["Konto"],
        "Debet": rad["Debet"],
        "Kredit": rad["Kredit"],
        "Beskrivning": beskrivning,
    }
    if har_kontonamn:
        f["Kontonamn"] = rad.get("Kontonamn", "")
    if har_text:
        f["Text"] = rad.get("Text", "")
    return f


def kontroll_balans(df):
    flaggor = []
    for ver_nr, grupp in df.groupby("Verifikationsnr"):
        saldo = grupp["Debet"].sum() - grupp["Kredit"].sum()
        if abs(saldo) > balans_tolerans:
            for _, rad in grupp.iterrows():
                flaggor.append(_flagga(
                    rad, "Obalans", "Hög", ver_nr,
                    f"Verifikation {ver_nr} är obalanserad med {saldo:.2f} kr",
                ))
    return flaggor


def kontroll_moms(df):
    flaggor = []
    alla_moms_konton = {moms_utg_25, moms_utg_12, moms_utg_6, moms_ing}
    for ver_nr, grupp in df.groupby("Verifikationsnr"):
        konton_i_ver = set(grupp["Konto"].values)
        for forsa_konto, forvantad_moms in forsakonto_moms.items():
            if forsa_konto in konton_i_ver:
                moms_i_ver = konton_i_ver & alla_moms_konton
                if moms_i_ver:
                    for moms_konto in moms_i_ver:
                        if moms_konto != forvantad_moms:
                            moms_rader = grupp[grupp["Konto"] == moms_konto]
                            for _, rad in moms_rader.iterrows():
                                flaggor.append(_flagga(
                                    rad, "Momsfel", "Hög", ver_nr,
                                    f"Konto {forsa_konto} förväntar moms på {forvantad_moms}, hittade {moms_konto}",
                                ))
    return flaggor


def kontroll_dubbletter(df):
    flaggor = []
    redan_flaggade = set()
    for i, rad1 in df.iterrows():
        belopp1 = rad1["Debet"] if rad1["Debet"] > 0 else rad1["Kredit"]
        if belopp1 == 0:
            continue
        for j, rad2 in df.iterrows():
            if j <= i:
                continue
            if (i, j) in redan_flaggade:
                continue
            if rad1["Konto"] != rad2["Konto"]:
                continue
            dagar = abs((rad1["Datum"] - rad2["Datum"]).days)
            if dagar > dubblett_dagar:
                continue
            if rad1["Verifikationsnr"] == rad2["Verifikationsnr"]:
                continue
            belopp2 = rad2["Debet"] if rad2["Debet"] > 0 else rad2["Kredit"]
            if belopp2 == 0:
                continue
            if belopp1 > 0:
                diff_pct = abs(belopp1 - belopp2) / belopp1 * 100
            else:
                continue
            if diff_pct <= dubblett_tolerans:
                redan_flaggade.add((i, j))
                exakt = "exakt" if diff_pct == 0 else f"inom {diff_pct:.1f}%"
                flaggor.append(_flagga(
                    rad1, "Möjlig dubblett", "Medium",
                    f"{rad1['Verifikationsnr']} / {rad2['Verifikationsnr']}",
                    f"Konto {rad1['Konto']}: {belopp1:.2f} kr ({exakt}) ver {rad1['Verifikationsnr']} & {rad2['Verifikationsnr']}, {dagar} dagar",
                ))
    return flaggor


def kontroll_kontokombinationer(df):
    flaggor = []
    kombos = {}
    for ver_nr, grupp in df.groupby("Verifikationsnr"):
        konton = tuple(sorted(grupp["Konto"].unique()))
        kombos[konton] = kombos.get(konton, 0) + 1
    totalt = sum(kombos.values())
    for ver_nr, grupp in df.groupby("Verifikationsnr"):
        konton = tuple(sorted(grupp["Konto"].unique()))
        if kombos[konton] == 1 and totalt > 10:
            for _, rad in grupp.iterrows():
                flaggor.append(_flagga(
                    rad, "Ovanlig kombination", "Låg", ver_nr,
                    f"Kontokombination {konton} förekommer bara 1 gång",
                ))
    return flaggor


def kontroll_periodisering(df):
    flaggor = []
    if not period_konto_ranges:
        return flaggor

    for _, rad in df.iterrows():
        konto = rad["Konto"]
        i_intervall = any(lo <= konto <= hi for lo, hi in period_konto_ranges)
        if not i_intervall:
            continue

        belopp = rad["Debet"] if rad["Debet"] > 0 else rad["Kredit"]
        if belopp < period_troskel:
            continue

        datum = rad["Datum"]
        sista_dag = calendar.monthrange(datum.year, datum.month)[1]
        ar_manadsslut = datum.day == sista_dag

        beskrivning = f"Stort belopp ({belopp:,.0f} kr) på kostnadskonto {konto}"
        if ar_manadsslut:
            beskrivning += " — bokförd på månadens sista dag, möjlig periodiseringskandidat"
        else:
            beskrivning += " — kan behöva periodiseras"

        flaggor.append(_flagga(
            rad, "Periodisering", "Medium", rad["Verifikationsnr"], beskrivning,
        ))
    return flaggor


def kontroll_loner(df):
    """Kontrollera löneskatt på pension, semesterlön med tillägg och AG-avgifter per individ."""
    flaggor = []
    if not har_text:
        return flaggor

    # Extrahera individnamn från Text-fältet
    # Förväntat format: "Typ Namn" t.ex. "Pension Anna Svensson", "SLP pension Erik Lindberg"

    # Gruppera per månad
    df_med_manad = df.copy()
    df_med_manad["Månad"] = df_med_manad["Datum"].dt.to_period("M")

    for manad, manad_df in df_med_manad.groupby("Månad"):
        # Hitta pensionsposter per individ
        pension_poster = manad_df[manad_df["Konto"] == cfg_konto_pension]
        for _, p_rad in pension_poster.iterrows():
            text = p_rad.get("Text", "")
            if not text:
                continue
            # Extrahera namn: ta bort "Pension " prefix
            namn = text.replace("Pension ", "").strip()
            if not namn:
                continue

            pension_belopp = p_rad["Debet"] if p_rad["Debet"] > 0 else p_rad["Kredit"]
            forvantad_slp = round(pension_belopp * cfg_loneskatt_sats, 2)

            # Hitta matchande SLP-post
            slp_poster = manad_df[
                (manad_df["Konto"] == cfg_konto_slp) &
                (manad_df["Text"].str.contains(namn, na=False))
            ]

            if slp_poster.empty:
                # SLP saknas helt
                flaggor.append(_flagga(
                    p_rad, "Löneskatt", "Hög", p_rad["Verifikationsnr"],
                    f"SLP saknas för {namn} ({manad}). Förväntat: {forvantad_slp:,.2f} kr "
                    f"({cfg_loneskatt_sats*100:.2f}% × {pension_belopp:,.2f} kr pension)",
                ))
            else:
                for _, s_rad in slp_poster.iterrows():
                    bokford_slp = s_rad["Debet"] if s_rad["Debet"] > 0 else s_rad["Kredit"]
                    diff = abs(bokford_slp - forvantad_slp)
                    if diff > cfg_tolerans_lon:
                        flaggor.append(_flagga(
                            s_rad, "Löneskatt", "Hög", s_rad["Verifikationsnr"],
                            f"SLP fel för {namn} ({manad}). Bokfört: {bokford_slp:,.2f} kr, "
                            f"förväntat: {forvantad_slp:,.2f} kr "
                            f"({cfg_loneskatt_sats*100:.2f}% × {pension_belopp:,.2f} kr). "
                            f"Differens: {diff:,.2f} kr",
                        ))

        # Hitta löner per individ för semesterberäkning
        lon_poster = manad_df[(manad_df["Konto"] == 7010) & (manad_df["Debet"] > 0)]
        for _, l_rad in lon_poster.iterrows():
            text = l_rad.get("Text", "")
            if not text:
                continue
            namn = text.replace("Lön ", "").strip()
            if not namn:
                continue

            lon_belopp = l_rad["Debet"]
            forvantad_semester = round(lon_belopp * cfg_semester_sats, 2)
            forvantad_tillagg = round(lon_belopp * cfg_semester_tillagg, 2)
            forvantad_semester_totalt = forvantad_semester + forvantad_tillagg
            forvantad_ag_semester = round(forvantad_semester_totalt * cfg_arbg_sats, 2)

            # Kontrollera semesterlöneskuld
            sem_poster = manad_df[
                (manad_df["Konto"] == cfg_konto_semlon) &
                (manad_df["Text"].str.contains(namn, na=False))
            ]
            for _, sem_rad in sem_poster.iterrows():
                bokford_sem = sem_rad["Debet"] if sem_rad["Debet"] > 0 else sem_rad["Kredit"]
                diff = abs(bokford_sem - forvantad_semester_totalt)
                if diff > cfg_tolerans_lon:
                    flaggor.append(_flagga(
                        sem_rad, "Semesterlön", "Medium", sem_rad["Verifikationsnr"],
                        f"Semesterlön fel för {namn} ({manad}). Bokfört: {bokford_sem:,.2f} kr, "
                        f"förväntat: {forvantad_semester_totalt:,.2f} kr "
                        f"({cfg_semester_sats*100:.1f}% + {cfg_semester_tillagg*100:.1f}% tillägg × {lon_belopp:,.0f} kr). "
                        f"Differens: {diff:,.2f} kr — saknas semesterlönetillägg?",
                    ))

            # Kontrollera AG-avgift på semesterlön
            ag_sem_poster = manad_df[
                (manad_df["Konto"] == cfg_konto_ag_sem) &
                (manad_df["Text"].str.contains(namn, na=False))
            ]
            for _, ag_rad in ag_sem_poster.iterrows():
                bokford_ag = ag_rad["Debet"] if ag_rad["Debet"] > 0 else ag_rad["Kredit"]
                diff = abs(bokford_ag - forvantad_ag_semester)
                if diff > cfg_tolerans_lon:
                    flaggor.append(_flagga(
                        ag_rad, "AG-avg semester", "Medium", ag_rad["Verifikationsnr"],
                        f"AG-avg semester fel för {namn} ({manad}). Bokfört: {bokford_ag:,.2f} kr, "
                        f"förväntat: {forvantad_ag_semester:,.2f} kr "
                        f"({cfg_arbg_sats*100:.2f}% × {forvantad_semester_totalt:,.2f} kr). "
                        f"Differens: {diff:,.2f} kr",
                    ))

    return flaggor


with st.spinner("Analyserar transaktioner..."):
    if kontroll_balans_aktiv:
        alla_flaggor.extend(kontroll_balans(df))
    if kontroll_moms_aktiv:
        alla_flaggor.extend(kontroll_moms(df))
    if kontroll_dubblett_aktiv:
        alla_flaggor.extend(kontroll_dubbletter(df))
    if kontroll_kombo_aktiv:
        alla_flaggor.extend(kontroll_kontokombinationer(df))
    if kontroll_period_aktiv:
        alla_flaggor.extend(kontroll_periodisering(df))
    if kontroll_lone_aktiv:
        alla_flaggor.extend(kontroll_loner(df))

if not alla_flaggor:
    st.markdown("""
    <div class="success-box">
        <div class="icon">✅</div>
        <h2>Inga avvikelser hittades</h2>
        <p>Alla kontroller passerade utan flaggningar.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

flaggor_df = pd.DataFrame(alla_flaggor)

n_hog = len(flaggor_df[flaggor_df["Allvarlighet"] == "Hög"])
n_medium = len(flaggor_df[flaggor_df["Allvarlighet"] == "Medium"])
n_lag = len(flaggor_df[flaggor_df["Allvarlighet"] == "Låg"])


# =====================================================
# RESULTAT
# =====================================================

# Metric-kort
st.markdown(f"""
<div class="metrics-row">
    <div class="metric-card mc-total">
        <div class="label">Totalt flaggade</div>
        <div class="value">{len(flaggor_df)}</div>
    </div>
    <div class="metric-card mc-hog">
        <div class="label">Hög</div>
        <div class="value">{n_hog}</div>
    </div>
    <div class="metric-card mc-medium">
        <div class="label">Medium</div>
        <div class="value">{n_medium}</div>
    </div>
    <div class="metric-card mc-lag">
        <div class="label">Låg</div>
        <div class="value">{n_lag}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Trafikljus — alla fynd sorterade per allvarlighet, sedan belopp (störst först)
tl_poster = flaggor_df.copy()
tl_poster["_belopp"] = tl_poster[["Debet", "Kredit"]].max(axis=1)

# Deduplicate per verifikation — behåll raden med högst belopp
tl_poster = tl_poster.sort_values("_belopp", ascending=False).drop_duplicates(subset=["Verifikationsnr", "Typ"], keep="first")

tl_config = [
    ("Hög", "hog", COLORS["hog"]),
    ("Medium", "medium", COLORS["medium"]),
    ("Låg", "lag", COLORS["lag"]),
]

for allv_namn, allv_key, _ in tl_config:
    grupp = tl_poster[tl_poster["Allvarlighet"] == allv_namn].sort_values("_belopp", ascending=False)
    if grupp.empty:
        continue

    total_belopp = grupp["_belopp"].sum()

    html = f"""<div class="tl-section">
    <div class="tl-header tl-{allv_key}">
        <span class="tl-dot d-{allv_key}"></span>
        {allv_namn} — {len(grupp)} poster — totalt {total_belopp:,.0f} kr
    </div>
    <div class="tl-list">"""

    for _, row in grupp.iterrows():
        belopp = row["_belopp"]
        datum_str = row["Datum"].strftime("%Y-%m-%d") if hasattr(row["Datum"], "strftime") else str(row["Datum"])
        typ_ikon = TYP_IKONER.get(row["Typ"], "")

        meta_parts = [f"Ver {row['Verifikationsnr']}", datum_str, f"Konto {int(row['Konto'])}"]
        if har_kontonamn and row.get("Kontonamn"):
            meta_parts[-1] += f" {row['Kontonamn']}"
        if har_text and row.get("Text"):
            meta_parts.append(row["Text"])

        html += f"""<div class="tl-item">
            <div>
                <div class="tl-desc">{typ_ikon} {row['Beskrivning']}</div>
                <div class="tl-meta">{' &middot; '.join(meta_parts)}</div>
            </div>
            <div class="tl-belopp b-{allv_key}">{belopp:,.0f} kr</div>
        </div>"""

    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)

# Tabs
tab_flaggor, tab_oversikt, tab_radata = st.tabs(["Flaggade poster", "Översikt", "Rådata"])


with tab_flaggor:
    # Filter
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    with filter_col1:
        filter_typ = st.multiselect(
            "Kontrolltyp", options=sorted(flaggor_df["Typ"].unique()),
            default=sorted(flaggor_df["Typ"].unique()),
        )
    with filter_col2:
        filter_allv = st.multiselect(
            "Allvarlighet", options=ALLV_ORDER, default=ALLV_ORDER,
        )
    with filter_col3:
        visa_som = st.radio("Visa som", ["Lista", "Tabell"], horizontal=True, label_visibility="collapsed")

    visade = flaggor_df[
        (flaggor_df["Typ"].isin(filter_typ)) & (flaggor_df["Allvarlighet"].isin(filter_allv))
    ].copy()

    st.caption(f"Visar {len(visade)} av {len(flaggor_df)} poster")

    if visa_som == "Lista":
        for typ_namn in sorted(visade["Typ"].unique()):
            typ_poster = visade[visade["Typ"] == typ_namn]
            ikon = TYP_IKONER.get(typ_namn, "")

            st.markdown(
                f'<div class="flagg-group-header">{ikon} {typ_namn} ({len(typ_poster)})</div>',
                unsafe_allow_html=True,
            )

            rows_html = '<div class="flagg-list">'
            for _, row in typ_poster.iterrows():
                allv = row["Allvarlighet"]
                allv_key = {"Hög": "hog", "Medium": "medium", "Låg": "lag"}.get(allv, "")
                belopp = row["Debet"] if row["Debet"] > 0 else row["Kredit"]
                datum_str = row["Datum"].strftime("%Y-%m-%d") if hasattr(row["Datum"], "strftime") else str(row["Datum"])

                meta_parts = [datum_str, f"Konto {int(row['Konto'])}"]
                if har_kontonamn and row.get("Kontonamn"):
                    meta_parts[-1] += f" {row['Kontonamn']}"
                meta_parts.append(f"{belopp:,.2f} kr")
                if har_text and row.get("Text"):
                    meta_parts.append(row["Text"])
                meta_str = " &middot; ".join(meta_parts)

                rows_html += f"""<div class="flagg-row">
                    <div class="flagg-stripe s-{allv_key}"></div>
                    <div class="flagg-badge b-{allv_key}">{allv}</div>
                    <div class="flagg-body">
                        <div class="flagg-desc">{row['Beskrivning']}</div>
                        <div class="flagg-meta">{meta_str}</div>
                    </div>
                    <div class="flagg-ver">Ver {row['Verifikationsnr']}</div>
                </div>"""

            rows_html += '</div>'
            st.markdown(rows_html, unsafe_allow_html=True)

    else:
        col_config = {
            "Allvarlighet": st.column_config.TextColumn("Allvarlighet", width="small"),
            "Typ": st.column_config.TextColumn("Typ", width="small"),
            "Datum": st.column_config.DateColumn("Datum", format="YYYY-MM-DD"),
            "Debet": st.column_config.NumberColumn("Debet", format="%.2f kr"),
            "Kredit": st.column_config.NumberColumn("Kredit", format="%.2f kr"),
            "Beskrivning": st.column_config.TextColumn("Beskrivning", width="large"),
        }
        col_order = ["Allvarlighet", "Typ", "Verifikationsnr", "Datum", "Konto"]
        if har_kontonamn:
            col_order.append("Kontonamn")
        col_order.extend(["Debet", "Kredit"])
        if har_text:
            col_order.append("Text")
        col_order.append("Beskrivning")

        st.dataframe(
            visade, use_container_width=True, height=500,
            column_config=col_config, column_order=col_order,
        )

    # Export
    def to_excel(export_df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Flaggade poster")
            workbook = writer.book
            worksheet = writer.sheets["Flaggade poster"]
            header_fmt = workbook.add_format({
                "bold": True, "bg_color": COLORS["primary"], "font_color": "white",
                "border": 1, "text_wrap": True, "valign": "vcenter",
            })
            for col_num, value in enumerate(export_df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)
            for i, col in enumerate(export_df.columns):
                max_len = max(export_df[col].astype(str).map(len).max(), len(col)) + 3
                worksheet.set_column(i, i, min(max_len, 60))
            worksheet.autofilter(0, 0, len(export_df), len(export_df.columns) - 1)
            worksheet.freeze_panes(1, 0)
        return output.getvalue()

    exp_col1, exp_col2 = st.columns([3, 1])
    with exp_col1:
        st.caption(f"Exportera {len(visade)} filtrerade poster till Excel med formatering och autofilter")
    with exp_col2:
        st.download_button(
            label="Ladda ner (.xlsx)",
            data=to_excel(visade),
            file_name="flaggade_poster.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


with tab_oversikt:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown('<div class="section-label">Per kontrolltyp</div>', unsafe_allow_html=True)
        typ_data = flaggor_df.groupby("Typ").size().reset_index(name="Antal")

        chart_typ = alt.Chart(typ_data).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Typ:N", axis=alt.Axis(labelAngle=-25, labelFontSize=11), title=None,
                     sort=list(TYP_COLORS.keys())),
            y=alt.Y("Antal:Q", title=None),
            color=alt.Color("Typ:N", scale=alt.Scale(
                domain=list(TYP_COLORS.keys()), range=list(TYP_COLORS.values()),
            ), legend=None),
            tooltip=["Typ", "Antal"],
        ).properties(height=280)

        text_typ = chart_typ.mark_text(dy=-10, fontSize=13, fontWeight="bold").encode(text="Antal:Q")
        st.altair_chart(chart_typ + text_typ, use_container_width=True)

    with chart_col2:
        st.markdown('<div class="section-label">Per allvarlighetsgrad</div>', unsafe_allow_html=True)
        allv_data = flaggor_df.groupby("Allvarlighet").size().reset_index(name="Antal")

        chart_allv = alt.Chart(allv_data).mark_arc(innerRadius=50, cornerRadius=3).encode(
            theta=alt.Theta("Antal:Q"),
            color=alt.Color("Allvarlighet:N", scale=alt.Scale(
                domain=ALLV_ORDER, range=ALLV_COLORS,
            ), legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["Allvarlighet", "Antal"],
        ).properties(height=280)
        st.altair_chart(chart_allv, use_container_width=True)

    st.markdown('<div class="section-label">Flaggningar över tid</div>', unsafe_allow_html=True)
    tid_data = flaggor_df.copy()
    tid_data["Vecka"] = tid_data["Datum"].dt.to_period("W").dt.start_time
    tid_summary = tid_data.groupby(["Vecka", "Allvarlighet"]).size().reset_index(name="Antal")

    chart_tid = alt.Chart(tid_summary).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("Vecka:T", title=None),
        y=alt.Y("Antal:Q", title=None, stack=True),
        color=alt.Color("Allvarlighet:N", scale=alt.Scale(
            domain=ALLV_ORDER, range=ALLV_COLORS,
        ), legend=alt.Legend(orient="top", title=None)),
        tooltip=["Vecka:T", "Allvarlighet", "Antal"],
    ).properties(height=220)
    st.altair_chart(chart_tid, use_container_width=True)


with tab_radata:
    st.caption(f"{len(df)} rader | {df['Verifikationsnr'].nunique()} verifikationer | {period_start} — {period_slut}")
    st.dataframe(
        df, use_container_width=True, height=600,
        column_config={
            "Datum": st.column_config.DateColumn("Datum", format="YYYY-MM-DD"),
            "Debet": st.column_config.NumberColumn("Debet", format="%.2f kr"),
            "Kredit": st.column_config.NumberColumn("Kredit", format="%.2f kr"),
        },
    )
