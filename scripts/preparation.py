from pathlib import Path
import re

import pandas as pd


# =====================================================
# 1. CONFIGURATION DU PROJET
# =====================================================

RACINE = Path(__file__).resolve().parents[1]

DOSSIER_RAW = RACINE / "data" / "raw"
DOSSIER_PROCESSED = RACINE / "data" / "processed"

FICHIER_EXCEL = DOSSIER_RAW / "EERH.xlsx"

DOSSIER_PROCESSED.mkdir(parents=True, exist_ok=True)


# =====================================================
# 2. IDENTIFIER L'ANNEE ET LE TRIMESTRE
# =====================================================

def analyser_periode(nom_colonne):
    """
    Extrait le trimestre et l'année du nom d'une colonne.

    Exemples :
    T1- 2019 -> année 2019, trimestre T1
    T4 -19   -> année 2019, trimestre T4
    T1-25    -> année 2025, trimestre T1
    """

    texte = str(nom_colonne).strip()

    correspondance = re.search(
        r"T([1-4])\s*[-–]?\s*(20\d{2}|\d{2})",
        texte,
        flags=re.IGNORECASE
    )

    if correspondance is None:
        return None

    trimestre = f"T{correspondance.group(1)}"
    annee = int(correspondance.group(2))

    if annee < 100:
        if annee == 19:
            annee = 2019
        else:
            annee = 2000 + annee

    return annee, trimestre


# =====================================================
# 3. NETTOYER LES NOMS DES SECTEURS
# =====================================================

def nettoyer_secteur(valeur):
    """Nettoie les espaces superflus sans changer le libellé."""

    if pd.isna(valeur):
        return None

    texte = str(valeur)
    texte = texte.replace("\xa0", " ")
    texte = re.sub(r"\s+", " ", texte)

    return texte.strip()


# =====================================================
# 4. TRANSFORMER UNE FEUILLE EN FORMAT LONG
# =====================================================

def transformer_feuille(df, nom_feuille):
    """
    Transforme les colonnes trimestrielles en lignes.
    """

    df = df.copy()

    # Nettoyer les noms de colonnes
    df.columns = [
        str(colonne).strip()
        for colonne in df.columns
    ]

    # La première colonne contient les secteurs
    colonne_secteur = df.columns[0]

    df = df.rename(
        columns={
            colonne_secteur: "secteur"
        }
    )

    df["secteur"] = df["secteur"].apply(
        nettoyer_secteur
    )

    # Identifier les colonnes correspondant aux trimestres
    colonnes_periodes = []

    for colonne in df.columns:
        if colonne == "secteur":
            continue

        periode = analyser_periode(colonne)

        if periode is not None:
            colonnes_periodes.append(colonne)

    if not colonnes_periodes:
        raise ValueError(
            f"Aucune colonne trimestrielle reconnue "
            f"dans la feuille {nom_feuille}."
        )

    # Passer du format large au format long
    df_long = df.melt(
        id_vars=["secteur"],
        value_vars=colonnes_periodes,
        var_name="periode_originale",
        value_name="valeur"
    )

    # Convertir les valeurs en nombres
    df_long["valeur"] = pd.to_numeric(
        df_long["valeur"],
        errors="coerce"
    )

    # Extraire l'année et le trimestre
    periodes = df_long["periode_originale"].apply(
        analyser_periode
    )

    df_long["annee"] = periodes.apply(
        lambda x: x[0] if x else None
    )

    df_long["trimestre"] = periodes.apply(
        lambda x: x[1] if x else None
    )

    # Identifier l'indicateur
    noms_indicateurs = {
        "Effectifs": "effectifs",
        "Rémunèration": "remuneration",
        "Remuneration": "remuneration",
        "Heure": "heures_travail"
    }

    df_long["indicateur"] = noms_indicateurs.get(
        nom_feuille,
        nom_feuille.lower()
    )

    # Organiser les colonnes
    df_long = df_long[
        [
            "indicateur",
            "secteur",
            "annee",
            "trimestre",
            "valeur"
        ]
    ]

    # Vérifications
    if df_long["annee"].isna().any():
        raise ValueError(
            f"Certaines années n'ont pas été reconnues "
            f"dans la feuille {nom_feuille}."
        )

    if df_long["trimestre"].isna().any():
        raise ValueError(
            f"Certains trimestres n'ont pas été reconnus "
            f"dans la feuille {nom_feuille}."
        )

    if df_long["valeur"].isna().any():
        raise ValueError(
            f"Des valeurs numériques sont manquantes "
            f"ou non reconnues dans la feuille {nom_feuille}."
        )

    return df_long


# =====================================================
# 5. PROGRAMME PRINCIPAL
# =====================================================

def main():

    if not FICHIER_EXCEL.exists():
        raise FileNotFoundError(
            f"Fichier Excel introuvable : {FICHIER_EXCEL}"
        )

    print("Lecture du fichier officiel :", FICHIER_EXCEL.name)

    classeur = pd.ExcelFile(FICHIER_EXCEL)

    tableaux_prepares = []

    for nom_feuille in classeur.sheet_names:

        print("\nTraitement de la feuille :", nom_feuille)

        df = pd.read_excel(
            FICHIER_EXCEL,
            sheet_name=nom_feuille
        )

        df_long = transformer_feuille(
            df,
            nom_feuille
        )

        nom_fichier = (
            nom_feuille.lower()
            .replace("è", "e")
            .replace("é", "e")
        )

        fichier_sortie = (
            DOSSIER_PROCESSED
            / f"{nom_fichier}_prepare.csv"
        )

        df_long.to_csv(
            fichier_sortie,
            index=False,
            encoding="utf-8-sig"
        )

        tableaux_prepares.append(df_long)

        print("Nombre de lignes :", len(df_long))
        print("Fichier créé :", fichier_sortie.name)

    # Regrouper les trois indicateurs dans un fichier unique
    df_complet = pd.concat(
        tableaux_prepares,
        ignore_index=True
    )

    fichier_complet = (
        DOSSIER_PROCESSED
        / "emploi_senegal_long.csv"
    )

    df_complet.to_csv(
        fichier_complet,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n====================================")
    print("PRÉPARATION TERMINÉE")
    print("====================================")

    print("Nombre total de lignes :", len(df_complet))

    print(
        "Années disponibles :",
        sorted(df_complet["annee"].unique())
    )

    print(
        "Indicateurs disponibles :",
        sorted(df_complet["indicateur"].unique())
    )

    print("\nAperçu des données préparées :")

    print(df_complet.head(10).to_string(index=False))

    print("\nFichier final :", fichier_complet)


if __name__ == "__main__":
    main()