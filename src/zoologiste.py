"""Web scraping : caractéristiques et photos des races de chats.

Le site sur lequel se base ce travail est une encyclopédie rassemblant
plusieurs espèces animales. Ce site comporte une page dédiée aux races de
chats, c'est celle-ci que nous voulons scrapper. Notre but est de reprendre
les caractéristiques disponibles pour chaque race, ainsi que la photo
associée. Nous utilisons `re` pour la partie des caractéristiques, et
BeautifulSoup pour les photos.
"""

import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
ESPECES_HTML_DIR = RAW_DIR / "especes_chats_html"
PICTURE_DIR = ROOT_DIR / "pictures"
DATA_CSV = ROOT_DIR / "data" / "chats_dataset.csv"

# Le site sert ses pages en UTF-8, mais son en-tête HTTP Content-Type n'indique pas
# de charset : requests retombe alors sur ISO-8859-1 par défaut et mal-décode les accents.
# On force explicitement l'encodage des réponses pour éviter ce mojibake.
ENCODING = "utf-8"
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv: 140.0) Gecko/20100101 Firefox/140.0"})

PATTERN_CARACTERISTIQUES = [
    "Origine", "Caractère", "Trait distinctif",
    "Niveau d'activité", "Santé", "Relations enfants", "Entretien du pelage",
    "Type de pelage", "Robe et couleurs", "Poids", "Taille", "Espérance de vie",
]


def get(url):
    req = session.get(url, timeout=10)
    req.encoding = ENCODING
    return req


def scrap_liste_especes():
    """Sauvegarde la page listant les races et en extrait les identifiants."""
    req_fullpage = get("https://www.zoologiste.com/chats/")
    with open(RAW_DIR / "zoologiste-chats.html", "w", encoding=ENCODING) as output:
        output.write(req_fullpage.text)

    pattern = '<a href="(.*?).html" class="titrelien"'
    return re.findall(pattern, req_fullpage.text)


def scrap_pages_especes(especes_chats):
    """Sauvegarde localement la page de chaque race."""
    ESPECES_HTML_DIR.mkdir(parents=True, exist_ok=True)
    for espece in especes_chats:
        req = get(f"https://www.zoologiste.com/chats/{espece}.html")
        with open(ESPECES_HTML_DIR / f"{espece}.html", "w", encoding=ENCODING) as output:
            output.write(req.text)


def extraire_caracteristiques(especes_chats):
    """Extrait les caractéristiques de chaque race depuis les pages locales."""
    final = []
    for espece in especes_chats:
        with open(ESPECES_HTML_DIR / f"{espece}.html", "r", encoding=ENCODING) as output:
            contenu = output.read()

        # N.B : r'...' est pour Raw String puisque | est reconnue comme l'opérateur logique "OU"
        pattern_nom = r"<title>(.*?) \| Race de chats</title>"
        result_nom = re.findall(pattern_nom, contenu)
        nom_final = result_nom[0].strip()
        infos_chats = {"Espèce": nom_final}

        for car in PATTERN_CARACTERISTIQUES:
            pattern_test = f"<li><span>{car} :</span> (.*?)</li>"
            result_caracteristiques = re.findall(pattern_test, contenu)
            if result_caracteristiques:
                infos_chats[car] = result_caracteristiques[0]
        final.append(infos_chats)

    return pd.DataFrame(final)


def scrap_photos():
    """Récupère la photo principale de chaque race, via BeautifulSoup."""
    PICTURE_DIR.mkdir(parents=True, exist_ok=True)

    link_png = []
    list_espece = []
    for html_page in ESPECES_HTML_DIR.iterdir():
        with open(html_page, "r", encoding=ENCODING) as output:
            content = output.read()

        content = BeautifulSoup(content, "html.parser")

        """
        Extrait de l'html que nous voulons récupérer
        <!-- main img -->
        <div class="col-sm-12 col-md-12 col-lg-6 col-xl-6 mainimg">
        <a data-fancybox="gallery" href="../images/xl/chat/balinais.jpg"><img src="../images/main/chat/balinais.jpg" alt="Balinais" title="Balinais" class="img-fluid" /></a>
        </div>
        <!-- / main img -->
        """
        part = content.find("div", class_="col-sm-12 col-md-12 col-lg-6 col-xl-6 mainimg")

        url_img = part.find("a").get("href")
        titre = part.find("img").get("alt")

        url_img = url_img.replace("..", "https://www.zoologiste.com/")
        req_img = session.get(url_img, timeout=10)  # binaire (image) : pas d'encodage texte à forcer

        link_png.append(url_img)
        list_espece.append(titre)

        with open(PICTURE_DIR / f"{titre}.png", "wb") as output:
            output.write(req_img.content)

    return pd.DataFrame({"Espèce": list_espece, "Lien PNG": link_png})


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    especes_chats = scrap_liste_especes()
    scrap_pages_especes(especes_chats)

    chats_dataset = extraire_caracteristiques(especes_chats)
    print(chats_dataset.head)

    df_link = scrap_photos()
    print(df_link)

    ### Réunion de l'ensemble des information sous un même dataset ###
    chats_dataset = chats_dataset.merge(df_link, how="inner", on="Espèce")
    print(chats_dataset)
    chats_dataset.to_csv(DATA_CSV, sep=",", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
