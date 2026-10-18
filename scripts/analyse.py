from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ==================================================
# 1. CONFIGURATION DU PROJET
# ==================================================

RACINE = Path(__file__).resolve().parents[1]

DOSSIER_DONNEES = RACINE / "data" / "processed"
DOSSIER_RAPPORTS = RACINE / "reports"
DOSSIER_GRAPHIQUES = DOSSIER_RAPPORTS / "figures"

FICHIER_DONNEES = DOSSIER_DONNEES / "emploi_senegal_long.csv"

DOSSIER_RAPPORTS.mkdir(parents=True, exist_ok=True)
DOSSIER_GRAPHIQUES.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. CHARGEMENT DES DONNEES
# ==================================================

def charger_donnees():
    if not FICHIER_DONNEES.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {FICHIER_DONNEES}"
        )

    df = pd.read_csv(FICHIER_DONNEES)

    colonnes_attendues = {
        "indicateur",
        "secteur",
        "annee",
        "trimestre",
        "valeur"
    }

    colonnes_manquantes = colonnes_attendues - set(df.columns)

    if colonnes_manquantes:
        raise ValueError(
            f"Colonnes manquantes : {colonnes_manquantes}"
        )

    df["annee"] = pd.to_numeric(df["annee"], errors="raise")
    df["valeur"] = pd.to_numeric(df["valeur"], errors="raise")

    print("\n======================================")
    print("CHARGEMENT DES DONNEES REUSSI")
    print("======================================")

    print("Nombre de lignes :", len(df))
    print("Nombre de colonnes :", len(df.columns))
    print("Années disponibles :", sorted(df["annee"].unique()))
    print("Indicateurs :", sorted(df["indicateur"].unique()))
    print("Secteurs :", df["secteur"].nunique())

    return df


# ==================================================
# 3. STATISTIQUES DESCRIPTIVES
# ==================================================

def statistiques_descriptives(df):
    print("\n======================================")
    print("STATISTIQUES DESCRIPTIVES")
    print("======================================")

    statistiques = (
        df.groupby("indicateur")["valeur"]
        .agg(["count", "mean", "median", "min", "max", "std"])
        .round(2)
    )

    print(statistiques.to_string())

    fichier_sortie = DOSSIER_RAPPORTS / "statistiques_descriptives.csv"
    statistiques.to_csv(fichier_sortie, encoding="utf-8-sig")

    print("\nFichier créé :", fichier_sortie)


# ==================================================
# 4. EVOLUTION TRIMESTRIELLE DES INDICATEURS
# ==================================================

def analyser_evolution(df):
    print("\n======================================")
    print("EVOLUTION DES INDICATEURS")
    print("======================================")

    ordre_trimestres = {
        "T1": 1,
        "T2": 2,
        "T3": 3,
        "T4": 4
    }

    df = df.copy()

    df["numero_trimestre"] = df["trimestre"].map(
        ordre_trimestres
    )

    df = df.sort_values(
        ["annee", "numero_trimestre"]
    )

    # Chaque indicateur est analysé séparément.
    # On ne somme pas les secteurs, car certains peuvent
    # représenter des totaux et d'autres des sous-secteurs.

    for indicateur in sorted(df["indicateur"].unique()):

        donnees = df[df["indicateur"] == indicateur]

        tableau = donnees.pivot_table(
            index=["annee", "trimestre", "numero_trimestre"],
            columns="secteur",
            values="valeur",
            aggfunc="first"
        )

        tableau = tableau.sort_index()

        print(f"\nIndicateur : {indicateur}")
        print("Nombre de périodes :", len(tableau))

        fichier_csv = (
            DOSSIER_RAPPORTS
            / f"evolution_{indicateur}.csv"
        )

        tableau.to_csv(fichier_csv, encoding="utf-8-sig")

        print("Tableau enregistré :", fichier_csv.name)

        # Création d'un graphique par indicateur.
        plt.figure(figsize=(12, 6))

        for secteur in tableau.columns:
            plt.plot(
                range(len(tableau)),
                tableau[secteur],
                marker="o",
                markersize=3,
                label=secteur
            )

        etiquettes = [
            f"{annee}-{trimestre}"
            for annee, trimestre, _ in tableau.index
        ]

        plt.xticks(
            range(len(etiquettes)),
            etiquettes,
            rotation=60
        )

        plt.title(
            f"Evolution trimestrielle : {indicateur}"
        )

        plt.xlabel("Période")
        plt.ylabel("Valeur observée")
        plt.grid(True, alpha=0.3)

        plt.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=7
        )

        plt.tight_layout()

        fichier_image = (
            DOSSIER_GRAPHIQUES
            / f"evolution_{indicateur}.png"
        )

        plt.savefig(fichier_image, dpi=150, bbox_inches="tight")
        plt.close()

        print("Graphique créé :", fichier_image.name)


# ==================================================
# 5. EVOLUTION ANNUELLE DES INDICATEURS
# ==================================================

def analyser_evolution_annuelle(df):
    print("\n======================================")
    print("EVOLUTION ANNUELLE")
    print("======================================")

    # Moyenne des valeurs trimestrielles pour chaque secteur.
    # Il s'agit d'une moyenne annuelle descriptive,
    # pas nécessairement d'un total annuel officiel.

    annuel = (
        df.groupby(["indicateur", "secteur", "annee"])["valeur"]
        .mean()
        .reset_index(name="moyenne_trimestrielle")
    )

    fichier_sortie = DOSSIER_RAPPORTS / "evolution_annuelle.csv"

    annuel.to_csv(
        fichier_sortie,
        index=False,
        encoding="utf-8-sig"
    )

    print("Fichier créé :", fichier_sortie)
    print("\nAperçu :")
    print(annuel.head(10).to_string(index=False))


# ==================================================
# 6. EXECUTION PRINCIPALE
# ==================================================

def main():
    df = charger_donnees()

    statistiques_descriptives(df)

    analyser_evolution(df)

    analyser_evolution_annuelle(df)

    print("\n======================================")
    print("ANALYSE TERMINEE AVEC SUCCES")
    print("======================================")

    print("Les résultats sont disponibles dans :")
    print(DOSSIER_RAPPORTS)


if __name__ == "__main__":
    main()