from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# CONFIGURATION
# =====================================================

RACINE = Path(__file__).resolve().parent

FICHIER_DONNEES = (
    RACINE
    / "data"
    / "processed"
    / "emploi_senegal_long.csv"
)

st.set_page_config(
    page_title="Sénégal Emploi Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================
# DESIGN BLEU NUIT ET BLANC
# =====================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F7FB;
    }

    [data-testid="stSidebar"] {
        background-color: #10243A;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF;
    }

    .hero {
        background: linear-gradient(120deg, #10243A, #1F4568);
        padding: 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
    }

    .hero h1 {
        color: white;
        font-size: 35px;
        margin-bottom: 8px;
    }

    .hero p {
        color: #DCE7F3;
        font-size: 16px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #DCE4EF;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 3px 10px rgba(16, 36, 58, 0.05);
    }

    h2, h3 {
        color: #10243A;
    }

    div[data-testid="stPlotlyChart"] {
        background: white;
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #DCE4EF;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# CHARGEMENT DES DONNEES
# =====================================================

@st.cache_data
def charger_donnees():
    if not FICHIER_DONNEES.exists():
        raise FileNotFoundError(
            f"Fichier de données introuvable : {FICHIER_DONNEES}"
        )

    df = pd.read_csv(FICHIER_DONNEES)

    colonnes = {
        "indicateur",
        "secteur",
        "annee",
        "trimestre",
        "valeur",
    }

    manquantes = colonnes - set(df.columns)

    if manquantes:
        raise ValueError(
            f"Colonnes manquantes dans le CSV : {manquantes}"
        )

    df["annee"] = pd.to_numeric(
        df["annee"], errors="raise"
    ).astype(int)

    df["valeur"] = pd.to_numeric(
        df["valeur"], errors="raise"
    )

    df["secteur"] = df["secteur"].astype(str).str.strip()
    df["indicateur"] = df["indicateur"].astype(str).str.strip()
    df["trimestre"] = df["trimestre"].astype(str).str.strip()

    return df


if not FICHIER_DONNEES.exists():
    st.error(
        "Le fichier de données est introuvable. "
        "Vérifie le dossier data/processed/."
    )
    st.stop()

try:
    df = charger_donnees()
except Exception as erreur:
    st.error(f"Impossible de charger les données : {erreur}")
    st.stop()


# =====================================================
# EN-TETE
# =====================================================

st.markdown(
    """
    <div class="hero">
        <h1>📊 Sénégal Emploi Analytics</h1>
        <p>
            Tableau de bord interactif consacré à l'exploration
            des données trimestrielles de l'emploi au Sénégal.
        </p>
        <p>
            Période disponible : 2019–2025 |
            Analyse sectorielle et temporelle
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# FILTRES
# =====================================================

st.sidebar.title("ESPACE D'ANALYSE")
st.sidebar.caption("Personnalise ton exploration des données")

noms_indicateurs = {
    "Effectifs": "effectifs",
    "Rémunération": "remuneration",
    "Heures de travail": "heures_travail",
}

choix = st.sidebar.selectbox(
    "Indicateur étudié",
    list(noms_indicateurs.keys()),
)

indicateur = noms_indicateurs[choix]

df_indicateur = df[
    df["indicateur"] == indicateur
].copy()

annees_disponibles = sorted(
    df_indicateur["annee"].unique().tolist()
)

annees_selectionnees = st.sidebar.multiselect(
    "Années",
    annees_disponibles,
    default=annees_disponibles,
)

secteurs_disponibles = sorted(
    df_indicateur["secteur"].dropna().unique().tolist()
)

secteurs_selectionnes = st.sidebar.multiselect(
    "Secteurs",
    secteurs_disponibles,
    default=secteurs_disponibles,
)

st.sidebar.markdown("---")

st.sidebar.info(
    "Les résultats sont descriptifs. "
    "Les unités et les définitions doivent être vérifiées "
    "avant toute conclusion économique."
)

if not annees_selectionnees or not secteurs_selectionnes:
    st.warning("Sélectionne au moins une année et un secteur.")
    st.stop()

donnees = df_indicateur[
    df_indicateur["annee"].isin(annees_selectionnees)
    & df_indicateur["secteur"].isin(secteurs_selectionnes)
].copy()

if donnees.empty:
    st.warning("Aucune donnée ne correspond à ces filtres.")
    st.stop()


# =====================================================
# PREPARATION DES PERIODES
# =====================================================

ordre_trimestres = {
    "T1": 1,
    "T2": 2,
    "T3": 3,
    "T4": 4,
}

donnees["numero_trimestre"] = (
    donnees["trimestre"].map(ordre_trimestres)
)

donnees = donnees.sort_values(
    ["annee", "numero_trimestre"]
)

donnees["periode"] = (
    donnees["annee"].astype(str)
    + "-"
    + donnees["trimestre"]
)


# =====================================================
# CARTES KPI
# =====================================================

st.subheader("Vue d'ensemble")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Observations",
        f"{len(donnees):,}".replace(",", " "),
    )

with k2:
    st.metric(
        "Secteurs sélectionnés",
        donnees["secteur"].nunique(),
    )

with k3:
    st.metric(
        "Années sélectionnées",
        donnees["annee"].nunique(),
    )

with k4:
    derniere_periode = donnees[
        ["annee", "numero_trimestre", "trimestre"]
    ].dropna().sort_values(
        ["annee", "numero_trimestre"]
    )

    if not derniere_periode.empty:
        ligne = derniere_periode.iloc[-1]
        texte_periode = f"{int(ligne['annee'])}-{ligne['trimestre']}"
    else:
        texte_periode = "Non disponible"

    st.metric(
        "Dernière période",
        texte_periode,
    )


# =====================================================
# EVOLUTION TEMPORELLE
# =====================================================

st.markdown("---")
st.subheader(f"📈 Évolution trimestrielle — {choix}")

fig_evolution = px.line(
    donnees,
    x="periode",
    y="valeur",
    color="secteur",
    markers=True,
    labels={
        "periode": "Période",
        "valeur": "Valeur observée",
        "secteur": "Secteur",
    },
    template="plotly_white",
)

fig_evolution.update_layout(
    height=500,
    hovermode="x unified",
    legend_title_text="Secteur",
    margin=dict(l=20, r=20, t=30, b=70),
)

fig_evolution.update_xaxes(tickangle=-45)

st.plotly_chart(
    fig_evolution,
    use_container_width=True,
)


# =====================================================
# COMPARAISON DES SECTEURS
# =====================================================

st.markdown("---")
st.subheader("📊 Comparaison descriptive des secteurs")

comparaison = (
    donnees.groupby("secteur", as_index=False)["valeur"]
    .mean()
    .rename(columns={"valeur": "moyenne_observee"})
    .sort_values("moyenne_observee", ascending=False)
)

fig_comparaison = px.bar(
    comparaison,
    x="moyenne_observee",
    y="secteur",
    orientation="h",
    labels={
        "moyenne_observee": "Moyenne observée",
        "secteur": "Secteur",
    },
    template="plotly_white",
)

fig_comparaison.update_layout(
    height=max(400, len(comparaison) * 30),
    yaxis={"categoryorder": "total ascending"},
    margin=dict(l=20, r=20, t=30, b=30),
)

st.plotly_chart(
    fig_comparaison,
    use_container_width=True,
)

st.caption(
    "La moyenne est calculée sur les observations filtrées. "
    "Elle est descriptive et ne constitue pas nécessairement "
    "un classement officiel. Les agrégats et sous-secteurs "
    "peuvent se chevaucher."
)


# =====================================================
# EVOLUTION ANNUELLE
# =====================================================

st.markdown("---")
st.subheader("📅 Évolution annuelle descriptive")

annuel = (
    donnees.groupby(["annee", "secteur"], as_index=False)["valeur"]
    .mean()
    .rename(columns={"valeur": "moyenne_trimestrielle"})
)

fig_annuel = px.line(
    annuel,
    x="annee",
    y="moyenne_trimestrielle",
    color="secteur",
    markers=True,
    labels={
        "annee": "Année",
        "moyenne_trimestrielle": "Moyenne des valeurs trimestrielles",
        "secteur": "Secteur",
    },
    template="plotly_white",
)

fig_annuel.update_layout(
    height=450,
    hovermode="x unified",
    legend_title_text="Secteur",
)

st.plotly_chart(
    fig_annuel,
    use_container_width=True,
)

st.caption(
    "Cette visualisation présente une moyenne des valeurs trimestrielles "
    "disponibles pour chaque secteur et chaque année. "
    "Elle ne doit pas être interprétée comme un total annuel."
)


# =====================================================
# TABLEAU DETAILLE
# =====================================================

st.markdown("---")
st.subheader("📋 Données détaillées")

colonnes = [
    "indicateur",
    "secteur",
    "annee",
    "trimestre",
    "valeur",
]

st.dataframe(
    donnees[colonnes],
    use_container_width=True,
    hide_index=True,
)


# =====================================================
# TELECHARGEMENT
# =====================================================

csv = donnees[colonnes].to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="📥 Télécharger les données filtrées",
    data=csv,
    file_name="senegal_emploi_donnees.csv",
    mime="text/csv",
)


# =====================================================
# METHODOLOGIE
# =====================================================

st.markdown("---")

with st.expander("ℹ️ À propos, source et méthodologie"):

    st.markdown(
        """
        **Projet :** Sénégal Emploi Analytics

        **Source :** fichier Excel de l'ANSD utilisé pour ce projet.
        Le titre exact de la publication et son lien officiel restent
        à documenter.

        **Technologies :** Python, Pandas, Plotly et Streamlit.

        **Indicateurs étudiés :**
        - Effectifs
        - Rémunération
        - Heures de travail

        **Période :** 2019–2025.

        **Méthodologie :** préparation des données, contrôle de qualité,
        statistiques descriptives et visualisations interactives.

        **Limites :** les unités, les définitions des indicateurs et
        les relations entre agrégats et sous-secteurs doivent être
        vérifiées dans la documentation méthodologique de la source
        avant toute interprétation économique.
        """
    )


# =====================================================
# PIED DE PAGE
# =====================================================

st.markdown("---")

st.caption(
    "Sénégal Emploi Analytics | Projet de portfolio "
    "en analyse de données | 2019–2025"
)