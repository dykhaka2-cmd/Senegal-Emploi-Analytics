from pathlib import Path

import pandas as pd


# ============================================
# CONFIGURATION
# ============================================

RACINE = Path(__file__).resolve().parents[1]

FICHIER = (
    RACINE
    / "data"
    / "processed"
    / "emploi_senegal_long.csv"
)

DOSSIER_RAPPORTS = RACINE / "reports"
DOSSIER_RAPPORTS.mkdir(parents=True, exist_ok=True)

FICHIER_SORTIE = DOSSIER_RAPPORTS / "controle_qualite.csv"


# ============================================
# CHARGEMENT
# ============================================

def main():

    print("=" * 60)
    print("CONTROLE QUALITE DES DONNEES")
    print("=" * 60)

    df = pd.read_csv(FICHIER)

    # Nettoyage léger des libellés
    df["secteur"] = (
        df["secteur"]
        .astype("string")
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    df["indicateur"] = (
        df["indicateur"]
        .astype("string")
        .str.strip()
    )

    # ============================================
    # 1. VERIFICATION DES VALEURS MANQUANTES
    # ============================================

    print("\n1. VALEURS MANQUANTES")

    print(df.isna().sum().to_string())

    # ============================================
    # 2. VERIFICATION DES DOUBLONS
    # ============================================

    print("\n2. DOUBLONS")

    cles = [
        "indicateur",
        "secteur",
        "annee",
        "trimestre"
    ]

    nombre_doublons = df.duplicated(
        subset=cles
    ).sum()

    print("Nombre de doublons :", nombre_doublons)

    # ============================================
    # 3. IDENTIFICATION DES LIGNES GLOBALES
    # ============================================

    print("\n3. LIGNES GLOBALES")

    lignes_globales = {
        "effectifs": "EFFECTIF",
        "remuneration": "Rémunération moyenne globale",
        "heures_travail": "Heure moyenne hebdomadaire globale"
    }

    for indicateur, libelle in lignes_globales.items():

        selection = df[
            (df["indicateur"] == indicateur)
            & (df["secteur"].str.casefold() == libelle.casefold())
        ]

        print(
            f"{indicateur} : "
            f"{len(selection)} observations globales identifiées"
        )

    # ============================================
    # 4. IDENTIFICATION DES LIBELLES A EXAMINER
    # ============================================

    print("\n4. LIBELLES A EXAMINER")

    motifs = ["dont", "industrie", "services"]

    selection = df[
        df["secteur"].str.lower().apply(
            lambda texte: any(
                motif in texte for motif in motifs
            )
        )
    ]

    print(
        selection[["indicateur", "secteur"]]
        .drop_duplicates()
        .sort_values(["indicateur", "secteur"])
        .to_string(index=False)
    )

    # ============================================
    # 5. CONTROLE DES VALEURS NUMERIQUES
    # ============================================

    print("\n5. CONTROLE NUMERIQUE")

    print("Valeurs non numériques :",
          pd.to_numeric(df["valeur"], errors="coerce").isna().sum())

    print("Valeurs négatives :", (df["valeur"] < 0).sum())

    print("Nombre total d'observations :", len(df))

    # ============================================
    # 6. EXPORT DU RAPPORT
    # ============================================

    rapport = pd.DataFrame({
        "controle": [
            "nombre_observations",
            "valeurs_manquantes",
            "doublons",
            "valeurs_negatives"
        ],
        "resultat": [
            len(df),
            int(df.isna().sum().sum()),
            int(nombre_doublons),
            int((df["valeur"] < 0).sum())
        ]
    })

    rapport.to_csv(
        FICHIER_SORTIE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 60)
    print("CONTROLE TERMINE")
    print("=" * 60)

    print("Rapport créé :", FICHIER_SORTIE)


if __name__ == "__main__":
    main()