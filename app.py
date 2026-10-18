from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


# ==================================================
# CONFIGURATION
# ==================================================

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
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1 {
        font-weight: 800;
    }

    [data-testid="stMetric"] {
        background-color: #f0f5fa;
        border: 1px solid #d9e2ec;
        padding: 18px;
        border-radius: 12px;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# CHARGEMENT DES DONNEES
# ==================================================

@st.cache_data
def charger_donnees():
    df = pd.read_csv(FICHIER_DONNEES)

    df["annee"] = pd.to_numeric(
        df["annee"],
        errors="raise"
    ).astype(int)

    df["valeur"] = pd.to_numeric(
        df["valeur"],
        errors="raise"
    )

    df["secteur"] = (
        df["secteur"]
        .astype(str)
        .str.strip()
    )

    df["indicateur"] = (
        df["indicateur"]
        .astype(str)
        .str.strip()
    )

    return df


# ==================================================
# TITRE
# ==================================================

st.title("📊 Sénégal Emploi Analytics")

st.subheader(
    "Exploration des données trimestrielles de l'emploi au Sénégal"
)

st.markdown(
    """
    Ce tableau de bord permet d'explorer les données d'effectifs,
    de rémunération et d'heures de travail issues du fichier Excel
    utilisé pour ce projet.

    Les résultats doivent être interprétés selon les définitions,
    les unités et la méthodologie de la source.
    """
)
with st.expander("À propos du projet"):

    st.markdown(
        """
        **Sénégal Emploi Analytics** est un projet de portfolio
        consacré à l'exploration des données trimestrielles de l'emploi.

        **Indicateurs étudiés :**
        - Effectifs
        - Rémunération
        - Heures de travail

        **Période étudiée :** 2019–2025.

        **Source des données :** fichier Excel de l'ANSD utilisé
        dans ce projet.

        **Objectif :** explorer les évolutions temporelles et comparer
        les valeurs observées selon les secteurs.

        **Limites :** les unités, les définitions des indicateurs et
        les relations entre secteurs et agrégats doivent être vérifiées
        dans la documentation méthodologique avant toute conclusion.
        """
    )

if not FICHIER_DONNEES.exists():
    st.error(
        "Le fichier de données est introuvable : "
        "data/processed/emploi_senegal_long.csv"
    )
    st.stop()

df = charger_donnees()


# ==================================================
# FILTRES
# ==================================================

st.sidebar.header("Filtres")

indicateurs = {
    "Effectifs": "effectifs",
    "Rémunération": "remuneration",
    "Heures de travail": "heures_travail"
}

choix_indicateur = st.sidebar.selectbox(
    "Choisir un indicateur",
    list(indicateurs.keys())
)

indicateur = indicateurs[choix_indicateur]

donnees_indicateur = df[
    df["indicateur"] == indicateur
].copy()

annees_disponibles = sorted(
    donnees_indicateur["annee"].unique()
)

annees_choisies = st.sidebar.multiselect(
    "Choisir les années",
    annees_disponibles,
    default=annees_disponibles
)

secteurs_disponibles = sorted(
    donnees_indicateur["secteur"].dropna().unique()
)

secteurs_choisis = st.sidebar.multiselect(
    "Choisir les secteurs",
    secteurs_disponibles,
    default=secteurs_disponibles
)

if not annees_choisies or not secteurs_choisis:
    st.warning(
        "Sélectionne au moins une année et un secteur."
    )
    st.stop()

donnees_filtrees = donnees_indicateur[
    donnees_indicateur["annee"].isin(annees_choisies)
    & donnees_indicateur["secteur"].isin(secteurs_choisis)
].copy()

ordre_trimestres = {
    "T1": 1,
    "T2": 2,
    "T3": 3,
    "T4": 4
}

donnees_filtrees["numero_trimestre"] = (
    donnees_filtrees["trimestre"]
    .map(ordre_trimestres)
)

donnees_filtrees = donnees_filtrees.sort_values(
    ["annee", "numero_trimestre"]
)

donnees_filtrees["periode"] = (
    donnees_filtrees["annee"].astype(str)
    + "-"
    + donnees_filtrees["trimestre"].astype(str)
)


# ==================================================
# INDICATEURS CLES
# ==================================================

st.markdown("---")
st.header("Vue d'ensemble")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Observations affichées",
        f"{len(donnees_filtrees):,}".replace(",", " ")
    )

with col2:
    st.metric(
        "Secteurs sélectionnés",
        donnees_filtrees["secteur"].nunique()
    )

with col3:
    st.metric(
        "Années sélectionnées",
        donnees_filtrees["annee"].nunique()
    )


# ==================================================
# GRAPHIQUE D'EVOLUTION
# ==================================================

st.markdown("---")
st.header("Évolution trimestrielle")

fig_evolution = px.line(
    donnees_filtrees,
    x="periode",
    y="valeur",
    color="secteur",
    markers=True,
    title=f"Évolution de l'indicateur : {choix_indicateur}",
    labels={
        "periode": "Période",
        "valeur": "Valeur observée",
        "secteur": "Secteur"
    }
)

fig_evolution.update_layout(
    xaxis_tickangle=-45,
    legend_title_text="Secteur",
    hovermode="x unified"
)

st.plotly_chart(
    fig_evolution,
    use_container_width=True
)


# ==================================================
# COMPARAISON DES SECTEURS
# ==================================================

st.markdown("---")
st.header("Comparaison des secteurs")

st.caption(
    "La moyenne ci-dessous est calculée sur les trimestres "
    "sélectionnés. Elle est descriptive et ne constitue pas "
    "nécessairement un classement officiel."
)

comparaison = (
    donnees_filtrees
    .groupby("secteur", as_index=False)["valeur"]
    .mean()
    .rename(columns={"valeur": "moyenne_observee"})
    .sort_values("moyenne_observee", ascending=False)
)

fig_comparaison = px.bar(
    comparaison,
    x="secteur",
    y="moyenne_observee",
    title="Moyenne observée par secteur",
    labels={
        "secteur": "Secteur",
        "moyenne_observee": "Moyenne observée"
    }
)

fig_comparaison.update_layout(
    xaxis_tickangle=-60
)

st.plotly_chart(
    fig_comparaison,
    use_container_width=True
)


# ==================================================
# TABLEAU DES DONNEES
# ==================================================

st.markdown("---")
st.header("Données détaillées")

colonnes = [
    "indicateur",
    "secteur",
    "annee",
    "trimestre",
    "valeur"
]

st.dataframe(
    donnees_filtrees[colonnes],
    use_container_width=True,
    hide_index=True
)


# ==================================================
# TELECHARGEMENT
# ==================================================

csv = donnees_filtrees[colonnes].to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="Télécharger les données filtrées en CSV",
    data=csv,
    file_name="donnees_emploi_senegal.csv",
    mime="text/csv"
)


# ==================================================
# PIED DE PAGE
# ==================================================

st.markdown("---")

st.caption(
    "Projet de portfolio : Sénégal Emploi Analytics. "
    "Les interprétations économiques nécessitent la vérification "
    "des unités, des définitions et des agrégats de la source."
)