from pathlib import Path

import pandas as pd


# Localisation du projet
RACINE = Path(__file__).resolve().parents[1]

# Dossier des données originales
DOSSIER_RAW = RACINE / "data" / "raw"


def trouver_fichier_excel():
    """Recherche un fichier Excel dans le dossier raw."""

    fichiers = list(DOSSIER_RAW.glob("*.xlsx"))
    fichiers += list(DOSSIER_RAW.glob("*.xls"))

    if not fichiers:
        raise FileNotFoundError(
            "Aucun fichier Excel trouvé dans data/raw."
        )

    if len(fichiers) > 1:
        raise RuntimeError(
            "Plusieurs fichiers Excel trouvés. "
            "Conserve un seul fichier pour cette étape."
        )

    return fichiers[0]


def diagnostic():
    """Examine les feuilles et les données du classeur."""

    fichier = trouver_fichier_excel()

    print("Fichier :", fichier.name)

    classeur = pd.ExcelFile(fichier)

    print("\nNombre de feuilles :", len(classeur.sheet_names))

    for nom_feuille in classeur.sheet_names:
        print("\n" + "=" * 60)
        print("FEUILLE :", nom_feuille)
        print("=" * 60)

        df = pd.read_excel(
            fichier,
            sheet_name=nom_feuille
        )

        print("\nDimensions :", df.shape)

        print("\nColonnes détectées :")
        print(df.columns.tolist())

        print("\nPremières lignes :")
        print(df.head(5).to_string(index=False))

        print("\nValeurs manquantes par colonne :")
        print(df.isna().sum().to_string())

        print("\nTypes de données :")
        print(df.dtypes.to_string())


if __name__ == "__main__":
    diagnostic()