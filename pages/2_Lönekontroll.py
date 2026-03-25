"""
Lönekontroll — semesterlöneskuld, pensionsavsättning och löneskatt per individ.
"""

import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Lönekontroll",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Färgpalett ---
COLORS = {
    "primary": "#1e3a5f",
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

_SP = '<div style="height:0.6rem"></div>'

# --- CSS ---
st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    html, body, [class*="st-"] {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        color: {COLORS["text"]};
    }}

    .app-header {{
        background: linear-gradient(135deg, #1a3a2d 0%, #276749 50%, #38a169 100%);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        margin-bottom: 1.4rem;
        color: white;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 20px rgba(26, 58, 45, 0.15);
        position: relative; overflow: hidden;
    }}
    .app-header::before {{
        content: ''; position: absolute;
        top: -40%; right: -10%; width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }}
    .app-header-left {{ position: relative; z-index: 1; }}
    .app-header-left h1 {{ margin: 0; font-size: 1.6rem; font-weight: 700; }}
    .app-header-left p {{ margin: 0.3rem 0 0 0; opacity: 0.75; font-size: 0.88rem; }}
    .app-header .badge {{
        position: relative; z-index: 1;
        background: rgba(255,255,255,0.12);
        padding: 0.3rem 0.9rem; border-radius: 20px;
        font-size: 0.68rem; letter-spacing: 0.05em; font-weight: 500;
        border: 1px solid rgba(255,255,255,0.15);
    }}

    .metrics-row {{
        display: flex; gap: 0.75rem; margin-bottom: 1.2rem;
    }}
    .metric-card {{
        flex: 1; border-radius: 16px; padding: 1.1rem;
        text-align: center; border: 1px solid {COLORS["border"]};
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }}
    .metric-card .label {{
        font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 0.2rem;
    }}
    .metric-card .value {{
        font-size: 1.5rem; font-weight: 700; line-height: 1.2;
    }}
    .mc-total {{ background: {COLORS["bg_subtle"]}; }}
    .mc-total .label {{ color: {COLORS["text_muted"]}; }}
    .mc-total .value {{ color: {COLORS["primary"]}; }}
    .mc-medium {{ background: {COLORS["medium_bg"]}; border-color: {COLORS["medium_border"]}; }}
    .mc-medium .label, .mc-medium .value {{ color: {COLORS["medium"]}; }}
    .mc-hog {{ background: {COLORS["hog_bg"]}; border-color: {COLORS["hog_border"]}; }}
    .mc-hog .label, .mc-hog .value {{ color: {COLORS["hog"]}; }}

    .section-label {{
        font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.06em; color: {COLORS["text_muted"]};
        margin-bottom: 0.5rem;
    }}
    .ctrl-label {{
        font-size: 0.85rem; font-weight: 600; color: {COLORS["text"]};
        margin-bottom: 0.25rem;
    }}

    /* Segmented tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background: #e8ecf1;
        border-radius: 22px;
        padding: 3px; gap: 2px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 20px !important;
        padding: 0.5rem 1.3rem;
        font-size: 0.88rem; font-weight: 500;
        transition: all 0.2s ease;
    }}
    .stTabs [aria-selected="true"] {{
        background: white !important;
        box-shadow: 0 1px 6px rgba(0,0,0,0.1);
        font-weight: 600;
    }}
    .stTabs [aria-selected="false"] {{
        background: transparent !important;
    }}

    /* Sidebar segmented */
    section[data-testid="stSidebar"] {{ background: {COLORS["bg_subtle"]}; }}
    section[data-testid="stSidebar"] .stRadio > div {{
        display: flex !important;
        background: #e8ecf1; border-radius: 22px; padding: 3px; gap: 2px;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label {{
        flex: 1; border-radius: 20px; padding: 0.35rem 0;
        font-size: 0.78rem; font-weight: 500; text-align: center;
        cursor: pointer; transition: all 0.2s ease;
        color: {COLORS["text_muted"]}; background: transparent; margin: 0;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"] > div:first-child {{
        display: none !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {{
        background: #38a169; color: white;
        box-shadow: 0 1px 6px rgba(56, 161, 105, 0.3); font-weight: 600;
    }}
    section[data-testid="stSidebar"] .stRadio p {{
        font-size: 0.78rem !important;
    }}

    .stDataFrame {{ border-radius: 14px !important; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }}
    button[kind="secondary"], .stDownloadButton > button {{ border-radius: 12px !important; }}
</style>
""", unsafe_allow_html=True)


# --- Header ---
st.markdown("""
<div class="app-header">
    <div class="app-header-left">
        <h1>Lönekontroll</h1>
        <p>Semesterlöneskuld, pensionsavsättning och löneskatt</p>
    </div>
    <span class="badge">LOKAL HANTERING</span>
</div>
""", unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    st.markdown("### Satser")

    cfg_arbg = st.number_input("Arbetsgivaravgift %", value=31.42, step=0.01, key="s_arbg") / 100
    cfg_skatt_tabell = st.number_input("Källskatt (skattetabell)", value=30.0, step=0.5, key="s_skatt",
                                        help="Genomsnittlig skattesats för beräkning") / 100

    st.markdown(_SP, unsafe_allow_html=True)
    st.markdown("### Konton")
    with st.expander("Bokföringskonton", expanded=False):
        k_lon = st.number_input("Lönekostnad", value=7010, step=1, key="s_k_lon")
        k_skatt = st.number_input("Källskatt", value=2710, step=1, key="s_k_skatt")
        k_netto = st.number_input("Nettolön (bank)", value=1930, step=1, key="s_k_netto")
        k_arbg = st.number_input("AG-avgift kostnad", value=7510, step=1, key="s_k_arbg")
        k_arbg_skuld = st.number_input("AG-avgift skuld", value=2730, step=1, key="s_k_arbg_skuld")


# --- Anställda ---
st.markdown('<div class="ctrl-label">Anställda</div>', unsafe_allow_html=True)

datakalla = st.radio("Datakälla", ["Manuell inmatning", "Ladda upp lönefil"], horizontal=True, key="datakalla", label_visibility="collapsed")

if datakalla == "Ladda upp lönefil":
    _, up_col, _ = st.columns([0.15, 0.7, 0.15])
    with up_col:
        lonefil = st.file_uploader(
            "Ladda upp lönefil (Excel/CSV)",
            type=["xlsx", "xls", "csv"],
            help="Kolumner: Namn, Bruttolön. Valfritt: Skattetabell %.",
            key="lonefil_upload",
        )

    if lonefil is not None:
        try:
            if lonefil.name.endswith(".csv"):
                lon_df = pd.read_csv(lonefil, sep=";", decimal=",")
                if len(lon_df.columns) <= 1:
                    lonefil.seek(0)
                    lon_df = pd.read_csv(lonefil, sep=",", decimal=".")
            else:
                lon_df = pd.read_excel(lonefil)
        except Exception as e:
            st.error(f"Kunde inte läsa filen: {e}")
            st.stop()

        LONE_ALIAS = {
            "Namn": ["name", "anställd", "employee", "förnamn", "efternamn", "namn"],
            "Bruttolön": ["lön", "lon", "månadslön", "salary", "grundlön", "bruttolön", "monthly_salary"],
            "Skatt %": ["skatt", "skattetabell", "skattesats", "tax"],
        }
        col_map = {}
        for target, aliases in LONE_ALIAS.items():
            if target in lon_df.columns:
                col_map[target] = target
            else:
                lower = {c.lower().strip(): c for c in lon_df.columns}
                for a in aliases:
                    if a.lower() in lower:
                        col_map[target] = lower[a.lower()]
                        break

        if "Namn" not in col_map or "Bruttolön" not in col_map:
            st.error("Kunde inte hitta kolumnerna Namn och Bruttolön/Månadslön.")
            st.stop()

        rename = {v: k for k, v in col_map.items() if v != k}
        lon_df = lon_df.rename(columns=rename)
        lon_df["Bruttolön"] = pd.to_numeric(lon_df["Bruttolön"], errors="coerce").fillna(0)
        if "Skatt %" not in lon_df.columns:
            lon_df["Skatt %"] = cfg_skatt_tabell * 100
        anst_data = lon_df[["Namn", "Bruttolön", "Skatt %"]].copy()
        st.success(f"Laddade {len(anst_data)} anställda från {lonefil.name}")
    else:
        st.info("Ladda upp en lönefil med kolumnerna **Namn** och **Bruttolön**.")
        st.stop()
else:
    if "lone_anst" not in st.session_state:
        st.session_state.lone_anst = pd.DataFrame([
            {"Namn": "Anna Svensson", "Bruttolön": 45000, "Skatt %": 30.0},
            {"Namn": "Erik Lindberg", "Bruttolön": 38000, "Skatt %": 28.0},
            {"Namn": "Maria Johansson", "Bruttolön": 52000, "Skatt %": 33.0},
            {"Namn": "Karl Nilsson", "Bruttolön": 41000, "Skatt %": 30.0},
            {"Namn": "Sara Eriksson", "Bruttolön": 35000, "Skatt %": 27.0},
        ])
    anst_data = st.session_state.lone_anst

anst_data["Bruttolön"] = pd.to_numeric(anst_data["Bruttolön"], errors="coerce").fillna(0).astype(float)
anst_data["Skatt %"] = pd.to_numeric(anst_data["Skatt %"], errors="coerce").fillna(30).astype(float)

edited = st.data_editor(
    anst_data,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Namn": st.column_config.TextColumn("Namn", width="medium"),
        "Bruttolön": st.column_config.NumberColumn("Bruttolön (kr)", format="%.0f", min_value=0),
        "Skatt %": st.column_config.NumberColumn("Skatt %", format="%.1f", min_value=0, max_value=60),
    },
    key="anst_edit",
)

st.markdown(_SP, unsafe_allow_html=True)

# --- Beräkning ---
st.markdown('<div class="ctrl-label">Lönespecifikation per anställd</div>', unsafe_allow_html=True)

rader = []
for _, row in edited.iterrows():
    brutto = row["Bruttolön"]
    skatt_pct = row["Skatt %"] / 100
    kallskatt = round(brutto * skatt_pct, 2)
    netto = round(brutto - kallskatt, 2)
    arbg = round(brutto * cfg_arbg, 2)
    total_kostnad = round(brutto + arbg, 2)

    rader.append({
        "Namn": row["Namn"],
        "Bruttolön": brutto,
        "Källskatt": kallskatt,
        "Nettolön": netto,
        "AG-avgift": arbg,
        "Total lönekostnad": total_kostnad,
    })

res_df = pd.DataFrame(rader)
for c in ["Bruttolön", "Källskatt", "Nettolön", "AG-avgift", "Total lönekostnad"]:
    res_df[c] = pd.to_numeric(res_df[c], errors="coerce").fillna(0).astype(float)

st.dataframe(
    res_df, use_container_width=True, hide_index=True,
    column_config={
        "Bruttolön": st.column_config.NumberColumn("Bruttolön", format="%.2f"),
        "Källskatt": st.column_config.NumberColumn("Källskatt", format="%.2f"),
        "Nettolön": st.column_config.NumberColumn("Nettolön", format="%.2f"),
        "AG-avgift": st.column_config.NumberColumn("AG-avgift", format="%.2f"),
        "Total lönekostnad": st.column_config.NumberColumn("Total lönekostnad", format="%.2f"),
    },
)

# Summering
tot_brutto = res_df["Bruttolön"].sum()
tot_skatt = res_df["Källskatt"].sum()
tot_netto = res_df["Nettolön"].sum()
tot_arbg = res_df["AG-avgift"].sum()
tot_kostnad = res_df["Total lönekostnad"].sum()

st.markdown(f"""
<div class="metrics-row">
    <div class="metric-card mc-total" style="border-radius: 14px;">
        <div class="label">Total bruttolön</div>
        <div class="value">{tot_brutto:,.0f} kr</div>
    </div>
    <div class="metric-card mc-medium" style="border-radius: 14px;">
        <div class="label">Källskatt</div>
        <div class="value">{tot_skatt:,.0f} kr</div>
    </div>
    <div class="metric-card mc-total" style="border-radius: 14px;">
        <div class="label">AG-avgifter</div>
        <div class="value">{tot_arbg:,.0f} kr</div>
    </div>
    <div class="metric-card mc-hog" style="border-radius: 14px;">
        <div class="label">Total kostnad</div>
        <div class="value">{tot_kostnad:,.0f} kr</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(_SP, unsafe_allow_html=True)

# Bokföringsförslag
st.markdown('<div class="ctrl-label">Bokföringsförslag</div>', unsafe_allow_html=True)
st.markdown(f"""
| Konto | Kontonamn | Debet | Kredit |
|------:|-----------|------:|-------:|
| {k_lon} | Lönekostnad | {tot_brutto:,.2f} kr | |
| {k_arbg} | Arbetsgivaravgifter | {tot_arbg:,.2f} kr | |
| {k_skatt} | Källskatt | | {tot_skatt:,.2f} kr |
| {k_arbg_skuld} | AG-avgifter skuld | | {tot_arbg:,.2f} kr |
| {k_netto} | Nettolön (utbetalning) | | {tot_netto:,.2f} kr |
""")

st.markdown(_SP, unsafe_allow_html=True)

# Export
def to_excel_lone():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        res_df.to_excel(writer, index=False, sheet_name="Lönespecifikation")
        bokf = pd.DataFrame([
            {"Konto": k_lon, "Kontonamn": "Lönekostnad", "Debet": tot_brutto, "Kredit": 0},
            {"Konto": k_arbg, "Kontonamn": "Arbetsgivaravgifter", "Debet": tot_arbg, "Kredit": 0},
            {"Konto": k_skatt, "Kontonamn": "Källskatt", "Debet": 0, "Kredit": tot_skatt},
            {"Konto": k_arbg_skuld, "Kontonamn": "AG-avgifter skuld", "Debet": 0, "Kredit": tot_arbg},
            {"Konto": k_netto, "Kontonamn": "Nettolön (utbetalning)", "Debet": 0, "Kredit": tot_netto},
        ])
        bokf.to_excel(writer, index=False, sheet_name="Bokföringsförslag")
        for sheet in writer.sheets:
            writer.sheets[sheet].freeze_panes(1, 0)
    return output.getvalue()

exp1, exp2 = st.columns([3, 1])
with exp1:
    st.caption("Exportera lönespecifikation och bokföringsförslag till Excel")
with exp2:
    st.download_button(
        "Ladda ner (.xlsx)",
        data=to_excel_lone(),
        file_name="lonekontroll.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
