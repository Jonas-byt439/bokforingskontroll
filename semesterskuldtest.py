"""Genererar en testfil för semesterskuldavstämning med 100+ anställda."""

import pandas as pd
import random

random.seed(123)

fornamn = [
    "Anna", "Erik", "Maria", "Karl", "Sara", "Johan", "Lisa", "Anders",
    "Emma", "Lars", "Karin", "Magnus", "Eva", "Mikael", "Helena", "Per",
    "Kristina", "Thomas", "Lena", "Fredrik", "Malin", "Henrik", "Susanne",
    "Patrik", "Elin", "Jonas", "Camilla", "Niklas", "Jenny", "Mattias",
    "Sofia", "Daniel", "Petra", "Martin", "Linda", "Andreas", "Johanna",
    "Rickard", "Sandra", "Oscar", "Hanna", "David", "Therese", "Gustaf",
    "Ida", "Viktor", "Cecilia", "Alexander", "Caroline", "Filip",
]

efternamn = [
    "Svensson", "Lindberg", "Johansson", "Nilsson", "Eriksson", "Bergström",
    "Andersson", "Holm", "Pettersson", "Karlsson", "Larsson", "Olsson",
    "Persson", "Gustafsson", "Jonsson", "Jansson", "Hansson", "Bengtsson",
    "Lindgren", "Lundberg", "Sjöberg", "Engström", "Lund", "Nordström",
    "Wallin", "Ström", "Berggren", "Sandberg", "Holmberg", "Nyström",
    "Forsberg", "Lindqvist", "Hedlund", "Wikström", "Sundberg", "Dahlberg",
    "Ekström", "Blom", "Fransson", "Löfgren", "Hellström", "Åberg",
    "Björk", "Månsson", "Lundgren", "Isaksson", "Abrahamsson", "Nordin",
    "Berglund", "Hägg",
]

ARBG_SATS = 0.3142
SEM_TILLAGG_SATS = 0.008  # 0.8% per månad

anstallda = []
anvanda_namn = set()

for i in range(110):
    # Generera unikt namn
    while True:
        fn = random.choice(fornamn)
        en = random.choice(efternamn)
        namn = f"{fn} {en}"
        if namn not in anvanda_namn:
            anvanda_namn.add(namn)
            break

    lon = random.randint(35000, 90000)
    manader = random.randint(1, 12)
    sem_dagar = random.choice([25, 25, 25, 25, 28, 30])  # De flesta har 25
    sparade = random.randint(0, 45)

    # Beräkna semesterlön: dagslön × (sem_dagar + sparade)
    dagslon = lon / 21
    sem_lon = round(dagslon * (sem_dagar + sparade), 2)
    sem_tillagg = round(lon * SEM_TILLAGG_SATS * manader, 2)
    ag_avg = round((sem_lon + sem_tillagg) * ARBG_SATS, 2)

    # Lägg in fel på ca 10% av posterna
    fel_typ = None
    if random.random() < 0.04:
        # AG-avgift saknas
        ag_avg = 0.0
        fel_typ = "AG saknas"
    elif random.random() < 0.05:
        # AG beräknad på fel underlag (på grundlön)
        ag_avg = round(lon * ARBG_SATS, 2)
        fel_typ = "AG på grundlön"
    elif random.random() < 0.04:
        # Semesterlön för hög (+15%)
        sem_lon = round(sem_lon * 1.15, 2)
        ag_avg = round((sem_lon + sem_tillagg) * ARBG_SATS, 2)
        fel_typ = "Sem.lön +15%"
    elif random.random() < 0.04:
        # Semestertillägg saknas
        sem_tillagg = 0.0
        ag_avg = round(sem_lon * ARBG_SATS, 2)
        fel_typ = "Tillägg saknas"
    elif random.random() < 0.03:
        # Sparade dagar ej medräknade
        sem_lon = round(dagslon * sem_dagar, 2)
        ag_avg = round((sem_lon + sem_tillagg) * ARBG_SATS, 2)
        if sparade > 0:
            fel_typ = "Sparade ej med"

    anstallda.append({
        "Namn": namn,
        "Månadslön": lon,
        "Antal månader": manader,
        "Semesterdagar": sem_dagar,
        "Sparade dagar": sparade,
        "Semesterlön (kr)": sem_lon,
        "Semestertillägg (kr)": sem_tillagg,
        "AG-avg (kr)": ag_avg,
        "_fel": fel_typ,
    })

df = pd.DataFrame(anstallda)

# Spara utan _fel-kolumnen
df_export = df.drop(columns=["_fel"])
df_export.to_excel("semesterskuldtest.xlsx", index=False, engine="openpyxl")
df_export.to_csv("semesterskuldtest.csv", index=False, sep=";", decimal=",")

# Statistik
fel_df = df[df["_fel"].notna()]
print(f"Genererade testfil med {len(df)} anställda")
print(f"Sparade: semesterskuldtest.xlsx och semesterskuldtest.csv")
print(f"\nSemesterlön: {df_export['Semesterlön (kr)'].min():,.0f} — {df_export['Semesterlön (kr)'].max():,.0f} kr")
print(f"Semestertillägg: {df_export['Semestertillägg (kr)'].min():,.0f} — {df_export['Semestertillägg (kr)'].max():,.0f} kr")
print(f"AG-avg: {df_export['AG-avg (kr)'].min():,.0f} — {df_export['AG-avg (kr)'].max():,.0f} kr")
print(f"Sparade dagar: 0 — {df['Sparade dagar'].max()}")
print(f"\nTotalt semesterlön: {df_export['Semesterlön (kr)'].sum():,.0f} kr")
print(f"Totalt semestertillägg: {df_export['Semestertillägg (kr)'].sum():,.0f} kr")
print(f"Totalt AG-avg: {df_export['AG-avg (kr)'].sum():,.0f} kr")
print(f"\nInlagda fel ({len(fel_df)} st):")
for _, r in fel_df.iterrows():
    print(f"  - {r['Namn']}: {r['_fel']} (sem.lön {r['Semesterlön (kr)']:,.0f}, tillägg {r['Semestertillägg (kr)']:,.0f}, AG {r['AG-avg (kr)']:,.0f})")
