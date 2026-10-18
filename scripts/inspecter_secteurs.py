from pathlib import Path

import pandas as pd


# Chemins du projet
RACINE = Path(__file__).resolve().parents[1]

FICHIER_EXCEL = RACINE / "data" / "raw" / "EERH.xlsx"

FICHIER_SORTIE = (
    RACINE
    / "reports"
    / "inventaire_secteurs.csv"
)

FICHIER_SORTIE.parent.mkdir(
    parents=True,
    exist_ok=True
)


def main():
    print("=" * 60)
    print("INSPECTION DES SECTEURS DE L'ANSD")
    print("=" * 60)

    if not FICHIER_EXCEL.exists():
        raise FileNotFoundError(
            f"Fichier Excel introuvable : {FICHIER_EXCEL}"
        )

    classeur = pd.ExcelFile(FICHIER_EXCEL)

    feuilles = []

    for nom_feuille in classeur.sheet_names:

        print(f"\nFeuille : {nom_feuille}")

        df = pd.read_excel(
            FICHIER_EXCEL,
            sheet_name=nom_feuille
        )

        colonne_secteur = df.columns[0]

        secteurs = (
            df[colonne_secteur]
            .dropna()
            .astype(str)
            .str.replace("\xa0", " ", regex=False)
            .str.strip()
            .drop_duplicates()
        )

        inventaire = pd.DataFrame({
            "feuille": nom_feuille,
            "secteur": secteurs
        })

        feuilles.append(inventaire)

        for i, secteur in enumerate(secteurs, start=1):
            print(f"{i:02d}. {secteur}")

    resultat = pd.concat(
        feuilles,
        ignore_index=True
    )

    resultat.to_csv(
        FICHIER_SORTIE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 60)
    print("INSPECTION TERMINEE")
    print("=" * 60)

    print("Nombre de lignes dans l'inventaire :", len(resultat))
    print("Fichier créé :", FICHIER_SORTIE)


if __name__ == "__main__":
    main()