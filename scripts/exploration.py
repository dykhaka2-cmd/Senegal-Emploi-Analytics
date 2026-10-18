from pathlib import Path

import pandas as pd


# Dossier principal du projet
RACINE = Path(__file__).resolve().parents[1]

# Dossier contenant les données originales
DOSSIER_DONNEES = RACINE / "data" / "raw"


def trouver_fichier_excel():
    """Recherche les fichiers Excel dans le dossier raw."""

    fichiers = list(DOSSIER_DONNEES.glob("*.xlsx"))

    if not fichiers:
        fichiers = list(DOSSIER_DONNEES.glob("*.xls"))

    if not fichiers:
        raise FileNotFoundError(
            "Aucun fichier Excel trouvé dans data/raw."
        )

    if len(fichiers) > 1:
        print("Plusieurs fichiers Excel ont été trouvés :")

        for fichier in fichiers:
            print("-", fichier.name)

        raise RuntimeError(
            "Garde un seul fichier Excel dans data/raw "
            "pour cette première exploration."
        )

    return fichiers[0]


def explorer_fichier(chemin):
    """Affiche les informations du classeur Excel."""

    print("\n===== FICHIER SÉLECTIONNÉ =====")
    print(chemin.name)

    classeur = pd.ExcelFile(chemin)

    print("\n===== FEUILLES DISPONIBLES =====")

    for feuille in classeur.sheet_names:
        print("-", feuille)

    for feuille in classeur.sheet_names:
        print(f"\n===== APERÇU : {feuille} =====")

        donnees = pd.read_excel(
            chemin,
            sheet_name=feuille,
            header=None,
            nrows=12
        )

        print(donnees.to_string(index=False, header=False))

        print("\nDimensions de l'aperçu :")
        print(donnees.shape)


def main():
    chemin = trouver_fichier_excel()
    explorer_fichier(chemin)


if __name__ == "__main__":
    main()