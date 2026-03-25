"""Genererar en exempelfil med transaktionsdata för test.

Innehåller medvetet inlagda fel:
- Momsfel (fel momskonto på försäljning)
- Felkonteringar (ovanliga kontokombinationer)
- Dubbletter (samma belopp nära i tid)
- Periodiseringsfel (helårsbelopp för hyra och försäkring bokförda i en klump)
"""

import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

# Kontoplan (förenklad)
konton = {
    1510: "Kundfordringar",
    1910: "Kassa",
    1930: "Företagskonto",
    1790: "Övriga förutbetalda kostnader",
    2440: "Leverantörsskulder",
    2960: "Övriga upplupna kostnader",
    2610: "Utgående moms 25%",
    2620: "Utgående moms 12%",
    2630: "Utgående moms 6%",
    2640: "Ingående moms",
    3010: "Försäljning varor 25%",
    3020: "Försäljning tjänster 25%",
    4010: "Inköp varor",
    5010: "Lokalhyra",
    5020: "Fastighetsskatt",
    5060: "Hyra av inventarier",
    5410: "Förbrukningsinventarier",
    6310: "Företagsförsäkring",
    6320: "Ansvarsförsäkring",
    6110: "Kontorsmaterial",
    6210: "Telefon",
    6250: "Porto",
    7010: "Löner",
    7510: "Arbetsgivaravgifter",
}

verifikationer = []
ver_nr = 1000

start_date = datetime(2025, 1, 1)


def rad(ver, datum, konto, debet, kredit, text):
    return {
        "Verifikationsnr": ver,
        "Datum": datum,
        "Konto": konto,
        "Kontonamn": konton[konto],
        "Debet": debet,
        "Kredit": kredit,
        "Text": text,
    }


# ===== NORMALA TRANSAKTIONER =====

for i in range(200):
    datum = start_date + timedelta(days=random.randint(0, 89))
    datum_str = datum.strftime("%Y-%m-%d")

    typ = random.choice(["försäljning", "inköp", "hyra", "lön", "övrigt"])

    if typ == "försäljning":
        belopp = round(random.uniform(5000, 150000), 2)
        moms = round(belopp * 0.25, 2)
        totalt = belopp + moms
        verifikationer.append(rad(ver_nr, datum_str, 1510, totalt, 0, f"Faktura F-{ver_nr}"))
        verifikationer.append(rad(ver_nr, datum_str, 3010, 0, belopp, f"Faktura F-{ver_nr}"))
        # Ibland: moms på fel konto (fel!)
        if random.random() < 0.05:
            moms_konto = random.choice([2620, 2630])
        else:
            moms_konto = 2610
        verifikationer.append(rad(ver_nr, datum_str, moms_konto, 0, moms, f"Faktura F-{ver_nr}"))

    elif typ == "inköp":
        belopp = round(random.uniform(1000, 50000), 2)
        moms = round(belopp * 0.25, 2)
        totalt = belopp + moms
        kostnads_konto = random.choice([4010, 5410, 6110, 6210])
        verifikationer.append(rad(ver_nr, datum_str, 2440, 0, totalt, f"Leverantörsfaktura LF-{ver_nr}"))
        # Ibland: konterat mot fel konto (fel!)
        if random.random() < 0.05:
            kostnads_konto = random.choice([7010, 6250])
        verifikationer.append(rad(ver_nr, datum_str, kostnads_konto, belopp, 0, f"Leverantörsfaktura LF-{ver_nr}"))
        verifikationer.append(rad(ver_nr, datum_str, 2640, moms, 0, f"Leverantörsfaktura LF-{ver_nr}"))

    elif typ == "hyra":
        # Normal månadshyra
        belopp = round(random.uniform(15000, 45000), 2)
        verifikationer.append(rad(ver_nr, datum_str, 5010, belopp, 0, "Lokalhyra"))
        verifikationer.append(rad(ver_nr, datum_str, 1930, 0, belopp, "Lokalhyra"))

    elif typ == "lön":
        belopp = round(random.uniform(25000, 55000), 2)
        arbg = round(belopp * 0.3142, 2)
        verifikationer.append(rad(ver_nr, datum_str, 7010, belopp, 0, "Lön"))
        verifikationer.append(rad(ver_nr, datum_str, 7510, arbg, 0, "Arbetsgivaravgifter"))
        verifikationer.append(rad(ver_nr, datum_str, 1930, 0, belopp + arbg, "Lön + arbetsgivaravgifter"))

    else:
        belopp = round(random.uniform(500, 10000), 2)
        verifikationer.append(rad(ver_nr, datum_str, 6110, belopp, 0, "Kontorsmaterial"))
        verifikationer.append(rad(ver_nr, datum_str, 1930, 0, belopp, "Kontorsmaterial"))

    ver_nr += 1


# ===== PERIODISERINGSFEL: HYRA =====

# Fel 1: Helårshyra bokförd i en klump i januari (borde periodiseras över 12 månader)
helars_hyra = 540000.00
verifikationer.append(rad(ver_nr, "2025-01-15", 5010, helars_hyra, 0, "Lokalhyra jan-dec 2025 — helårsavtal"))
verifikationer.append(rad(ver_nr, "2025-01-15", 1930, 0, helars_hyra, "Lokalhyra jan-dec 2025 — helårsavtal"))
ver_nr += 1

# Fel 2: Kvartalshyra bokförd i en klump (Q1, borde fördelas jan-mars)
kvartals_hyra = 180000.00
verifikationer.append(rad(ver_nr, "2025-01-02", 5010, kvartals_hyra, 0, "Lokalhyra Q1 2025 — kvartalsbetalning"))
verifikationer.append(rad(ver_nr, "2025-01-02", 2440, 0, kvartals_hyra, "Lokalhyra Q1 2025 — kvartalsbetalning"))
ver_nr += 1

# Fel 3: Hyra av inventarier, halvår i förskott
halvar_inventarier = 96000.00
verifikationer.append(rad(ver_nr, "2025-01-31", 5060, halvar_inventarier, 0, "Hyra kopiatorer jan-jun 2025"))
verifikationer.append(rad(ver_nr, "2025-01-31", 1930, 0, halvar_inventarier, "Hyra kopiatorer jan-jun 2025"))
ver_nr += 1


# ===== PERIODISERINGSFEL: FÖRSÄKRINGAR =====

# Fel 4: Helårsförsäkring bokförd rakt av i januari
helars_forsakring = 156000.00
verifikationer.append(rad(ver_nr, "2025-01-10", 6310, helars_forsakring, 0, "Företagsförsäkring 2025 — helårspremie"))
verifikationer.append(rad(ver_nr, "2025-01-10", 1930, 0, helars_forsakring, "Företagsförsäkring 2025 — helårspremie"))
ver_nr += 1

# Fel 5: Ansvarsförsäkring, kvartalspremie bokförd i en klump
kvartals_forsakring = 72000.00
verifikationer.append(rad(ver_nr, "2025-01-05", 6320, kvartals_forsakring, 0, "Ansvarsförsäkring Q1 2025"))
verifikationer.append(rad(ver_nr, "2025-01-05", 2440, 0, kvartals_forsakring, "Ansvarsförsäkring Q1 2025"))
ver_nr += 1

# Fel 6: Ny försäkring tecknad i mars, 9 månader framåt — ej periodiserad
nio_man_forsakring = 108000.00
verifikationer.append(rad(ver_nr, "2025-03-01", 6310, nio_man_forsakring, 0, "Tilläggsförsäkring mars-nov 2025"))
verifikationer.append(rad(ver_nr, "2025-03-01", 1930, 0, nio_man_forsakring, "Tilläggsförsäkring mars-nov 2025"))
ver_nr += 1


# ===== PERIODISERINGSFEL: ÖVRIGA =====

# Fel 7: Fastighetsskatt helår bokförd i februari
fastighetsskatt = 84000.00
verifikationer.append(rad(ver_nr, "2025-02-15", 5020, fastighetsskatt, 0, "Fastighetsskatt 2025"))
verifikationer.append(rad(ver_nr, "2025-02-15", 1930, 0, fastighetsskatt, "Fastighetsskatt 2025"))
ver_nr += 1


# ===== PERIODISERINGSFEL: LÖNESKATT PÅ PENSION =====

# Fel 8: Löneskatt på pensionsinsättning — helårsbelopp bokförd i en klump
# (Särskild löneskatt 24,26% på pensionskostnader, ska periodiseras månatligen)
konton[7410] = "Pensionskostnader"
konton[7530] = "Särskild löneskatt pensionskostnader"
konton[2920] = "Upplupna semesterlöner"
konton[2940] = "Upplupna arbetsgivaravgifter"
konton[7090] = "Förändring semesterlöneskuld"
konton[7519] = "Arbetsgivaravgifter semesterlön"

# --- Anställda för individberäkningar ---
anstallda = [
    {"namn": "Anna Svensson",  "lon": 45000},
    {"namn": "Erik Lindberg",  "lon": 38000},
    {"namn": "Maria Johansson","lon": 52000},
    {"namn": "Karl Nilsson",   "lon": 41000},
    {"namn": "Sara Eriksson",  "lon": 35000},
]

ARBG_SATS = 0.3142
LONESKATT_SATS = 0.2426
SEMESTER_SATS = 0.12      # 12% semesterlön
SEMESTER_TILLAGG = 0.008  # 0.8% semesterlönetillägg per månad
PENSION_SATS = 0.045      # 4.5% tjänstepension


# ===== LÖNEKÖRNINGAR PER MÅNAD PER INDIVID (jan-mars) =====

for manad in range(1, 4):  # jan, feb, mars
    datum_str = f"2025-{manad:02d}-25"

    for anst in anstallda:
        lon = anst["lon"]
        namn = anst["namn"]

        # --- Grundlön + arbetsgivaravgift ---
        arbg = round(lon * ARBG_SATS, 2)
        verifikationer.append(rad(ver_nr, datum_str, 7010, lon, 0, f"Lön {namn}"))
        verifikationer.append(rad(ver_nr, datum_str, 7510, arbg, 0, f"Arbetsgivaravgift {namn}"))
        verifikationer.append(rad(ver_nr, datum_str, 1930, 0, lon + arbg, f"Lön + AG-avg {namn}"))
        ver_nr += 1

        # --- Pension per individ ---
        pension = round(lon * PENSION_SATS, 2)
        loneskatt = round(pension * LONESKATT_SATS, 2)

        verifikationer.append(rad(ver_nr, datum_str, 7410, pension, 0, f"Pension {namn}"))
        verifikationer.append(rad(ver_nr, datum_str, 1930, 0, pension, f"Pension {namn}"))
        ver_nr += 1

        # FEL: Löneskatt beräknad med fel procent för vissa anställda
        if namn == "Erik Lindberg":
            # Fel: Använder 31.42% istället för 24.26%
            loneskatt_fel = round(pension * ARBG_SATS, 2)
            verifikationer.append(rad(ver_nr, datum_str, 7530, loneskatt_fel, 0, f"SLP pension {namn}"))
            verifikationer.append(rad(ver_nr, datum_str, 2960, 0, loneskatt_fel, f"SLP pension {namn}"))
        elif namn == "Sara Eriksson" and manad == 2:
            # Fel: Glömt att bokföra löneskatt i februari
            pass
        else:
            verifikationer.append(rad(ver_nr, datum_str, 7530, loneskatt, 0, f"SLP pension {namn}"))
            verifikationer.append(rad(ver_nr, datum_str, 2960, 0, loneskatt, f"SLP pension {namn}"))
        ver_nr += 1

        # --- Semesterlön per individ ---
        semester = round(lon * SEMESTER_SATS, 2)
        semester_tillagg = round(lon * SEMESTER_TILLAGG, 2)
        semester_totalt = semester + semester_tillagg
        arbg_semester = round(semester_totalt * ARBG_SATS, 2)

        # FEL: Karl Nilsson saknar semesterlönetillägg
        if namn == "Karl Nilsson":
            semester_bokfort = semester  # Saknar tillägget 0.8%
        else:
            semester_bokfort = semester_totalt

        verifikationer.append(rad(ver_nr, datum_str, 7090, semester_bokfort, 0, f"Semesterlöneskuld {namn}"))
        verifikationer.append(rad(ver_nr, datum_str, 2920, 0, semester_bokfort, f"Semesterlöneskuld {namn}"))
        ver_nr += 1

        # FEL: Maria Johansson har fel arbetsgivaravgift på semesterlön i mars
        if namn == "Maria Johansson" and manad == 3:
            # Beräknat på grundlön istället för semesterlön
            arbg_semester_fel = round(lon * ARBG_SATS, 2)
            verifikationer.append(rad(ver_nr, datum_str, 7519, arbg_semester_fel, 0, f"AG-avg semester {namn}"))
            verifikationer.append(rad(ver_nr, datum_str, 2940, 0, arbg_semester_fel, f"AG-avg semester {namn}"))
        else:
            verifikationer.append(rad(ver_nr, datum_str, 7519, arbg_semester, 0, f"AG-avg semester {namn}"))
            verifikationer.append(rad(ver_nr, datum_str, 2940, 0, arbg_semester, f"AG-avg semester {namn}"))
        ver_nr += 1


# ===== DUBBLETTER =====

for _ in range(5):
    idx = random.randint(0, len(verifikationer) - 1)
    dubblett = verifikationer[idx].copy()
    dubblett["Verifikationsnr"] = ver_nr
    if random.random() < 0.5:
        dubblett["Debet"] = round(dubblett["Debet"] * random.uniform(0.99, 1.01), 2) if dubblett["Debet"] > 0 else 0
        dubblett["Kredit"] = round(dubblett["Kredit"] * random.uniform(0.99, 1.01), 2) if dubblett["Kredit"] > 0 else 0
    verifikationer.append(dubblett)
    ver_nr += 1


# ===== SPARA =====

df = pd.DataFrame(verifikationer)
df = df.sort_values(["Datum", "Verifikationsnr"]).reset_index(drop=True)

df.to_excel("exempeldata.xlsx", index=False, engine="openpyxl")
df.to_csv("exempeldata.csv", index=False, sep=";", decimal=",")

print(f"Genererade {len(df)} rader med transaktionsdata")
print(f"Sparade: exempeldata.xlsx och exempeldata.csv")
print(f"\nKolumner: {list(df.columns)}")
print(f"\nInlagda periodiseringsfel:")
print(f"  - Helårshyra 540 000 kr (jan)")
print(f"  - Kvartalshyra 180 000 kr (jan)")
print(f"  - Hyra inventarier 96 000 kr halvår (jan)")
print(f"  - Företagsförsäkring 156 000 kr helår (jan)")
print(f"  - Ansvarsförsäkring 72 000 kr kvartal (jan)")
print(f"  - Tilläggsförsäkring 108 000 kr 9 mån (mars)")
print(f"  - Fastighetsskatt 84 000 kr helår (feb)")
print(f"\nInlagda lönefel (individnivå):")
print(f"  - Erik Lindberg: SLP beräknad med 31.42% istället för 24.26% (alla månader)")
print(f"  - Sara Eriksson: SLP saknas helt i februari")
print(f"  - Karl Nilsson: Semesterlönetillägg 0.8% saknas (alla månader)")
print(f"  - Maria Johansson: AG-avg på semester beräknad på grundlön istället för semesterlön (mars)")
