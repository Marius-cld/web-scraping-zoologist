"""Nettoyage du jeu de données scrappé et génération des graphiques."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT_DIR / "data" / "chats_dataset.csv"
FIGURE_DIR = ROOT_DIR / "figures"
TABLE_DIR = ROOT_DIR / "tables"


def nettoyer(df):
    ### Nettoyage ###
    df[["Poids min (kg)", "Poids max (kg)"]] = (
        df["Poids"]
        .str.replace("kg", "", regex=False)
        .str.split("-", expand=True)
    )

    df[["Espérance de vie min", "Espérance de vie max"]] = (
        df["Espérance de vie"]
        .str.replace("ans", "", regex=False)
        .str.split("-", expand=True)
    )

    cols_num = [
        "Poids min (kg)", "Poids max (kg)",
        "Espérance de vie min", "Espérance de vie max",
    ]
    df[cols_num] = df[cols_num].astype(float)
    df = df.drop(columns=["Poids", "Espérance de vie"])

    df["Continent"] = df["Origine"]

    afrique = ["Égypte ancienne"]
    asie = ["Turquie", "Russie", "Birmanie", "Japon", "Thaïlande", "Iran", "Singapour"]
    europe = ["Royaume-Uni", "France", "Europe", "Norvège", "Écosse"]
    amerique = ["États-Unis", "Canada"]

    df.loc[df["Origine"].isin(afrique), "Continent"] = "Afrique"
    df.loc[df["Origine"].isin(asie), "Continent"] = "Asie"
    df.loc[df["Origine"].isin(europe), "Continent"] = "Europe"
    df.loc[df["Origine"].isin(amerique), "Continent"] = "Amérique"

    df["Caractère_1"] = df["Caractère"].str.split(", ").str[0]
    df["Caractère_2"] = df["Caractère"].str.split(", ").str[1]

    df["Relations enfants"] = df["Relations enfants"].str.replace(" Amical", "Amical", regex=False)
    return df


def sauvegarder_statistiques_descriptives(df_num, df_cat):
    print(df_num.describe())
    print(df_cat.drop(columns=["Lien PNG"]).describe())

    with pd.ExcelWriter(TABLE_DIR / "resume_statistique.xlsx") as writer:
        df_num.describe().to_excel(writer, sheet_name="Numerique")
        df_cat.drop(columns=["Lien PNG"]).describe().to_excel(writer, sheet_name="Categoriel")


def generer_graphiques(df):
    sns.set_theme(style="whitegrid")

    # Activité
    ordre_activite = ["Faible", "Modéré", "Élevé", "Très élevé"]
    sns.catplot(data=df, x="Niveau d'activité", kind="count",
                order=ordre_activite, palette="pastel", height=7, aspect=1.5)
    plt.title("Nombre d'espèces de chats par niveau d'activité")
    plt.savefig(FIGURE_DIR / "activite.png")
    plt.show()

    # Origine / continent (pays regroupés par continent pour une lecture plus claire)
    ordre_continent = df.sort_values("Continent")["Origine"].unique()
    sns.catplot(data=df, x="Origine", kind="count", palette="pastel",
                hue="Continent", edgecolor=".6", order=ordre_continent)
    plt.xticks(rotation=45, ha="right")
    plt.title("Nombre d'espèces de chats par pays d'origine", fontsize=16)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "pays.png")
    plt.show()

    # Santé
    ordre_sante = ["Sensible", "Variable", "Bonne", "Robuste"]
    sns.catplot(data=df, x="Santé", kind="count",
                order=ordre_sante, palette="pastel")
    plt.title("Qualité de santé des chats")
    plt.savefig(FIGURE_DIR / "sante.png")
    plt.show()

    # Boxplot poids
    sns.boxplot(data=df[["Poids min (kg)", "Poids max (kg)"]], palette="pastel")
    plt.title("Répartition des poids")
    plt.ylabel("Poids (kg)")
    plt.savefig(FIGURE_DIR / "repartition_poids.png")
    plt.show()

    # Boxplot espérance de vie
    sns.boxplot(data=df[["Espérance de vie min", "Espérance de vie max"]], palette="pastel")
    plt.title("Répartition des espérances de vie")
    plt.ylabel("Années")
    plt.savefig(FIGURE_DIR / "repartition_vie.png")
    plt.show()

    # Top caractères
    caracteres = df["Caractère"].str.lower().str.split(", ").explode()
    top_caracteres = caracteres.value_counts().head(10)

    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_caracteres.values, y=top_caracteres.index, palette="pastel")
    plt.title("Top 10 des traits de caractère")
    plt.xlabel("Nombre")
    plt.ylabel("Caractère")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "top_caracteres.png")
    plt.show()


def main():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_CSV, sep=",")
    print(df.head())

    df = nettoyer(df)
    print(df.info())

    df_num = df.select_dtypes(include="number")
    df_cat = df.select_dtypes(exclude="number")
    sauvegarder_statistiques_descriptives(df_num, df_cat)

    generer_graphiques(df)


if __name__ == "__main__":
    main()
