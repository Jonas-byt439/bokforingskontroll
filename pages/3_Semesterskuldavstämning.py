"""
Semesterskuldavstämning — stäm av bokförd semesterlöneskuld mot beräknad.
"""

import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Semesterskuldavstämning",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
        background: linear-gradient(135deg, #1a365d 0%, #3182ce 50%, #63b3ed 100%);
        padding: 2rem 2.5rem; border-radius: 20px; margin-bottom: 1.4rem;
        color: white; display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 20px rgba(26, 54, 93, 0.15);
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

    .metrics-row {{ display: flex; gap: 0.75rem; margin-bottom: 1.2rem; }}
    .metric-card {{
        flex: 1; border-radius: 16px; padding: 1.1rem;
        text-align: center; border: 1px solid {COLORS["border"]};
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }}
    .metric-card .label {{
        font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 0.2rem;
    }}
    .metric-card .value {{ font-size: 1.5rem; font-weight: 700; line-height: 1.2; }}
    .mc-total {{ background: {COLORS["bg_subtle"]}; }}
    .mc-total .label {{ color: {COLORS["text_muted"]}; }}
    .mc-total .value {{ color: {COLORS["primary"]}; }}
    .mc-medium {{ background: {COLORS["medium_bg"]}; border-color: {COLORS["medium_border"]}; }}
    .mc-medium .label, .mc-medium .value {{ color: {COLORS["medium"]}; }}
    .mc-hog {{ background: {COLORS["hog_bg"]}; border-color: {COLORS["hog_border"]}; }}
    .mc-hog .label, .mc-hog .value {{ color: {COLORS["hog"]}; }}
    .mc-lag {{ background: {COLORS["lag_bg"]}; border-color: {COLORS["lag_border"]}; }}
    .mc-lag .label, .mc-lag .value {{ color: {COLORS["lag"]}; }}

    .ctrl-label {{
        font-size: 0.85rem; font-weight: 600; color: {COLORS["text"]};
        margin-bottom: 0.25rem;
    }}
    .section-label {{
        font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.06em; color: {COLORS["text_muted"]};
        margin-bottom: 0.5rem;
    }}

    .stDataFrame {{ border-radius: 14px !important; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }}
    button[kind="secondary"], .stDownloadButton > button {{ border-radius: 12px !important; }}

    section[data-testid="stSidebar"] {{ background: {COLORS["bg_subtle"]}; }}

    /* Diff-tabell */
    .diff-ok {{ color: {COLORS["lag"]}; font-weight: 600; }}
    .diff-warn {{ color: {COLORS["medium"]}; font-weight: 600; }}
    .diff-err {{ color: {COLORS["hog"]}; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)


# --- Header ---
st.markdown("""
<div class="app-header">
    <div class="app-header-left">
        <h1>Semesterskuldavstämning</h1>
        <p>Stäm av bokförd semesterlöneskuld mot beräknad skuld per anställd</p>
    </div>
    <span class="badge">LOKAL HANTERING</span>
</div>
""", unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    st.markdown("### Beräkningssatser")

    cfg_sem = st.number_input("Semesterlön %", value=12.0, step=0.1, key="av_sem") / 100
    cfg_tillagg = st.number_input("Tillägg %/mån", value=0.8, step=0.1, key="av_till") / 100
    cfg_arbg = st.number_input("AG-avgift %", value=31.42, step=0.01, key="av_arbg") / 100

    st.markdown(_SP, unsafe_allow_html=True)
    st.markdown("### Semesterdagar")
    cfg_sem_dagar = st.number_input("Semesterdagar/år", value=25, step=1, key="av_semdagar")
    cfg_arbetstagar_manad = st.number_input("Arbetsdagar/mån (snitt)", value=21, step=1, key="av_arbdagar")

    st.markdown(_SP, unsafe_allow_html=True)
    st.markdown("### Konton")
    k_uppl_sem = st.number_input("Upplupna semesterlöner", value=2920, step=1, key="av_k_sem")
    k_uppl_ag = st.number_input("Upplupna AG-avg", value=2940, step=1, key="av_k_ag")

    st.markdown(_SP, unsafe_allow_html=True)
    tolerans = st.number_input("Tolerans för avvikelse (kr)", value=100.0, step=50.0, key="av_tol")


# --- Steg 1: Anställda med löner ---
st.markdown('<div class="ctrl-label">1. Anställda och löner</div>', unsafe_allow_html=True)
st.caption("Ange anställda med månadslön och antal intjänade månader, eller ladda upp en lönefil.")

_, up_col, _ = st.columns([0.15, 0.7, 0.15])
with up_col:
    lonefil = st.file_uploader(
        "Ladda upp lönefil (valfritt)",
        type=["xlsx", "xls", "csv"],
        help="Kolumner: Namn, Månadslön. Valfritt: Antal månader.",
        key="av_lonefil",
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

    # Enkel automapping
    lower = {c.lower().strip(): c for c in lon_df.columns}
    col_map = {}
    for target, aliases in {"Namn": ["namn", "name", "anställd"], "Månadslön": ["månadslön", "lön", "lon", "salary", "grundlön"]}.items():
        if target in lon_df.columns:
            col_map[target] = target
        else:
            for a in aliases:
                if a in lower:
                    col_map[target] = lower[a]
                    break

    if "Namn" not in col_map or "Månadslön" not in col_map:
        st.error("Kunde inte hitta kolumnerna Namn och Månadslön. Kontrollera filen.")
        st.stop()

    rename = {v: k for k, v in col_map.items() if v != k}
    lon_df = lon_df.rename(columns=rename)
    lon_df["Månadslön"] = pd.to_numeric(lon_df["Månadslön"], errors="coerce").fillna(0)
    if "Antal månader" not in lon_df.columns:
        lon_df["Antal månader"] = 3
    if "Semesterdagar" not in lon_df.columns:
        lon_df["Semesterdagar"] = cfg_sem_dagar
    if "Sparade dagar" not in lon_df.columns:
        lon_df["Sparade dagar"] = 0
    if "Semesterdagar" not in lon_df.columns:
        lon_df["Semesterdagar"] = cfg_sem_dagar
    if "Sparade dagar" not in lon_df.columns:
        lon_df["Sparade dagar"] = 0
    anst_default = lon_df[["Namn", "Antal månader", "Semesterdagar", "Sparade dagar"]].copy()

    # Hämta belopp från filen om de finns
    fil_har_semlon = False
    for col_namn in ["Semesterlön (kr)", "Semesterlön", "semesterlön"]:
        if col_namn in lon_df.columns:
            anst_default["_fil_semlon"] = pd.to_numeric(lon_df[col_namn], errors="coerce").fillna(0)
            fil_har_semlon = True
            break
    fil_har_ag = False
    for col_namn in ["AG-avg (kr)", "AG-avg", "ag-avg"]:
        if col_namn in lon_df.columns:
            anst_default["_fil_ag"] = pd.to_numeric(lon_df[col_namn], errors="coerce").fillna(0)
            fil_har_ag = True
            break
    fil_har_tillagg = False
    for col_namn in ["Semestertillägg (kr)", "Semestertillägg", "semestertillägg"]:
        if col_namn in lon_df.columns:
            anst_default["_fil_tillagg"] = pd.to_numeric(lon_df[col_namn], errors="coerce").fillna(0)
            fil_har_tillagg = True
            break

    st.success(f"Laddade {len(anst_default)} anställda")
else:
    anst_default = pd.DataFrame([
        {"Namn": "Anna Svensson", "Antal månader": 3, "Semesterdagar": 25, "Sparade dagar": 5},
        {"Namn": "Erik Lindberg", "Antal månader": 3, "Semesterdagar": 25, "Sparade dagar": 0},
        {"Namn": "Maria Johansson", "Antal månader": 3, "Semesterdagar": 25, "Sparade dagar": 8},
        {"Namn": "Karl Nilsson", "Antal månader": 3, "Semesterdagar": 25, "Sparade dagar": 3},
        {"Namn": "Sara Eriksson", "Antal månader": 3, "Semesterdagar": 25, "Sparade dagar": 0},
    ])

anst = st.data_editor(
    anst_default, use_container_width=True, num_rows="dynamic",
    column_config={
        "Namn": st.column_config.TextColumn("Namn", width="medium"),
        "Antal månader": st.column_config.NumberColumn("Mån", min_value=1, max_value=12),
        "Semesterdagar": st.column_config.NumberColumn("Sem.dagar", min_value=0, max_value=35),
        "Sparade dagar": st.column_config.NumberColumn("Sparade", min_value=0, max_value=35, help="Sparade semesterdagar från tidigare år"),
    },
    key="av_anst",
)

st.markdown(_SP, unsafe_allow_html=True)

# --- Steg 2: Bokförda saldon ---
st.markdown('<div class="ctrl-label">2. Semesterlön</div>', unsafe_allow_html=True)
st.caption("Ange bokförd semesterlön per anställd eller som totalsaldo.")

bokf_metod = st.radio("Metod", ["Per anställd", "Totalsaldo"], horizontal=True, key="av_metod", label_visibility="collapsed")

if bokf_metod == "Per anställd":
    bokf_data = []
    for i, (_, row) in enumerate(anst.iterrows()):
        sem_val = 0.0
        ag_val = 0.0
        till_val = 0.0
        # Hämta från fil om tillgängligt
        if lonefil is not None and i < len(anst_default):
            if "_fil_semlon" in anst_default.columns:
                sem_val = float(anst_default.iloc[i].get("_fil_semlon", 0))
            if "_fil_ag" in anst_default.columns:
                ag_val = float(anst_default.iloc[i].get("_fil_ag", 0))
            if "_fil_tillagg" in anst_default.columns:
                till_val = float(anst_default.iloc[i].get("_fil_tillagg", 0))
        bokf_data.append({
            "Namn": row["Namn"],
            "Semesterlön (kr)": sem_val,
            "Semestertillägg (kr)": till_val,
            "AG-avg (kr)": ag_val,
        })
    bokf_df = pd.DataFrame(bokf_data)
    bokf_df["Semesterlön (kr)"] = pd.to_numeric(bokf_df["Semesterlön (kr)"], errors="coerce").fillna(0).astype(float)
    bokf_df["Semestertillägg (kr)"] = pd.to_numeric(bokf_df["Semestertillägg (kr)"], errors="coerce").fillna(0).astype(float)
    bokf_df["AG-avg (kr)"] = pd.to_numeric(bokf_df["AG-avg (kr)"], errors="coerce").fillna(0).astype(float)

    bokf_edit = st.data_editor(
        bokf_df, use_container_width=True, num_rows="fixed",
        column_config={
            "Namn": st.column_config.TextColumn("Namn", disabled=True, width="medium"),
            "Semesterlön (kr)": st.column_config.NumberColumn("Semesterlön (kr)", format="%.2f"),
            "Semestertillägg (kr)": st.column_config.NumberColumn("Tillägg (kr)", format="%.2f"),
            "AG-avg (kr)": st.column_config.NumberColumn("AG-avg (kr)", format="%.2f"),
        },
        key="av_bokf",
    )
else:
    bc1, bc2 = st.columns(2)
    with bc1:
        total_bokf_sem = st.number_input(f"Bokfört saldo konto {k_uppl_sem} (kr)", value=0.0, step=1000.0, key="av_tot_sem")
    with bc2:
        total_bokf_ag = st.number_input(f"Bokfört saldo konto {k_uppl_ag} (kr)", value=0.0, step=1000.0, key="av_tot_ag")

st.markdown(_SP, unsafe_allow_html=True)

# --- Steg 3: Beräkning & avstämning ---
st.markdown('<div class="ctrl-label">3. Avstämningsresultat</div>', unsafe_allow_html=True)

result_rows = []
total_tillagg_kr = 0

for i, (_, row) in enumerate(anst.iterrows()):
    man = row["Antal månader"]
    namn = row["Namn"]
    sem_dagar = row.get("Semesterdagar", cfg_sem_dagar)
    sparade = row.get("Sparade dagar", 0)
    totala_dagar = sem_dagar + sparade

    if bokf_metod == "Per anställd":
        bokf_sem = bokf_edit.iloc[i]["Semesterlön (kr)"] if i < len(bokf_edit) else 0
        bokf_tillagg = bokf_edit.iloc[i]["Semestertillägg (kr)"] if i < len(bokf_edit) else 0
        bokf_ag = bokf_edit.iloc[i]["AG-avg (kr)"] if i < len(bokf_edit) else 0
    else:
        total_dagar_alla = sum(
            r.get("Semesterdagar", cfg_sem_dagar) + r.get("Sparade dagar", 0)
            for _, r in anst.iterrows()
        )
        andel = totala_dagar / total_dagar_alla if total_dagar_alla > 0 else 0
        bokf_sem = round(total_bokf_sem * andel, 2)
        bokf_ag = round(total_bokf_ag * andel, 2)
        bokf_tillagg = 0.0

    total_tillagg_kr += bokf_tillagg

    result_rows.append({
        "Namn": namn,
        "Sem.dagar": int(sem_dagar),
        "Sparade": int(sparade),
        "Tot dagar": int(totala_dagar),
        "Semesterlön": bokf_sem,
        "Semestertillägg": bokf_tillagg,
        "AG-avg": bokf_ag,
        "Totalt inkl. tillägg": round(bokf_sem + bokf_tillagg, 2),
        "Totalt inkl. AG": round(bokf_sem + bokf_tillagg + bokf_ag, 2),
    })

res_df = pd.DataFrame(result_rows)


for c in ["Semesterlön", "Semestertillägg", "AG-avg", "Totalt inkl. tillägg", "Totalt inkl. AG"]:
    if c in res_df.columns:
        res_df[c] = pd.to_numeric(res_df[c], errors="coerce").fillna(0).astype(float)

st.dataframe(
    res_df, use_container_width=True, hide_index=True,
    column_config={
        "Sem.dagar": st.column_config.NumberColumn("Sem.dagar"),
        "Sparade": st.column_config.NumberColumn("Sparade"),
        "Tot dagar": st.column_config.NumberColumn("Tot dagar"),
        "Semesterlön": st.column_config.NumberColumn("Semesterlön", format="%.2f"),
        "Semestertillägg": st.column_config.NumberColumn("Semestertillägg", format="%.2f"),
        "AG-avg": st.column_config.NumberColumn("AG-avg", format="%.2f"),
        "Totalt inkl. tillägg": st.column_config.NumberColumn("Totalt inkl. tillägg", format="%.2f"),
        "Totalt inkl. AG": st.column_config.NumberColumn("Totalt inkl. AG", format="%.2f"),
    },
)

# Summering
tot_sem = res_df["Semesterlön"].sum()
tot_ag = res_df["AG-avg"].sum()
tot_inkl_tillagg = res_df["Totalt inkl. tillägg"].sum()
tot_allt = res_df["Totalt inkl. AG"].sum()

st.markdown(f"""
<div class="metrics-row">
    <div class="metric-card mc-total" style="border-radius: 14px;">
        <div class="label">Total semesterlön</div>
        <div class="value">{tot_sem:,.0f} kr</div>
    </div>
    <div class="metric-card mc-total" style="border-radius: 14px;">
        <div class="label">Semesterlönetillägg</div>
        <div class="value">{total_tillagg_kr:,.0f} kr</div>
    </div>
    <div class="metric-card mc-medium" style="border-radius: 14px;">
        <div class="label">AG-avgifter</div>
        <div class="value">{tot_ag:,.0f} kr</div>
    </div>
    <div class="metric-card mc-hog" style="border-radius: 14px;">
        <div class="label">Total semesterskuld</div>
        <div class="value">{tot_allt:,.0f} kr</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="metrics-row">
    <div class="metric-card mc-total" style="border-radius: 14px;">
        <div class="label">Totala semesterdagar</div>
        <div class="value">{res_df["Tot dagar"].sum()}</div>
    </div>
    <div class="metric-card mc-medium" style="border-radius: 14px;">
        <div class="label">Varav sparade</div>
        <div class="value">{res_df["Sparade"].sum()}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(_SP, unsafe_allow_html=True)

# Justeringsförslag
st.markdown('<div class="ctrl-label">Bokföringsförslag</div>', unsafe_allow_html=True)
st.markdown(f"""
| Konto | Kontonamn | Debet | Kredit |
|------:|-----------|------:|-------:|
| 7090 | Förändring semesterlöneskuld | {tot_inkl_tillagg:,.2f} kr | |
| 7519 | AG-avg semesterlön | {tot_ag:,.2f} kr | |
| {k_uppl_sem} | Upplupna semesterlöner | | {tot_inkl_tillagg:,.2f} kr |
| {k_uppl_ag} | Upplupna arbetsgivaravgifter | | {tot_ag:,.2f} kr |
""")

st.markdown(_SP, unsafe_allow_html=True)

# Export
def to_excel_avst():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        res_df.to_excel(writer, index=False, sheet_name="Avstämning")
        workbook = writer.book
        worksheet = writer.sheets["Avstämning"]
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": "#1a3a2d", "font_color": "white",
            "border": 1, "valign": "vcenter",
        })
        for col_num, value in enumerate(res_df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
        for i, col in enumerate(res_df.columns):
            max_len = max(res_df[col].astype(str).map(len).max(), len(col)) + 3
            worksheet.set_column(i, i, min(max_len, 30))
        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, len(res_df), len(res_df.columns) - 1)
    return output.getvalue()

exp1, exp2 = st.columns([3, 1])
with exp1:
    st.caption("Exportera avstämning till Excel")
with exp2:
    st.download_button(
        "Ladda ner (.xlsx)",
        data=to_excel_avst(),
        file_name="semesterskuldavstamning.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
