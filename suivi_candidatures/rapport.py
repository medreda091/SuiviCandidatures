"""Génération du rapport HTML : KPI, graphiques et interprétation.

Les graphiques sont dessinés en SVG directement, sans dépendance
externe : le rapport s'ouvre dans n'importe quel navigateur, même
sans installer de bibliothèque graphique.
"""

from html import escape

from .base import LIBELLES_STATUTS, STATUTS
from .statistiques import calculer


def _barres_svg(donnees, largeur=480, hauteur_barre=26):
    """Dessine un diagramme à barres horizontales en SVG.

    `donnees` est une liste de (libellé, valeur). Les valeurs nulles
    sont quand même affichées, pour que le graphique reste honnête.
    """
    maximum = max([valeur for _, valeur in donnees] + [1])
    hauteur = len(donnees) * (hauteur_barre + 8) + 10
    morceaux = [f'<svg width="{largeur}" height="{hauteur}"'
                ' xmlns="http://www.w3.org/2000/svg">']
    for i, (libelle, valeur) in enumerate(donnees):
        y = 10 + i * (hauteur_barre + 8)
        largeur_barre = int((valeur / maximum) * (largeur - 220)) if valeur else 0
        morceaux.append(
            f'<text x="0" y="{y + 17}" font-size="13">{escape(libelle)}</text>'
            f'<rect x="150" y="{y}" width="{largeur_barre}"'
            f' height="{hauteur_barre}" fill="#0f766e" rx="4" />'
            f'<text x="{155 + largeur_barre}" y="{y + 17}"'
            f' font-size="13">{valeur}</text>'
        )
    morceaux.append("</svg>")
    return "\n".join(morceaux)


def interpreter(stats):
    """Rédige en français ce que les chiffres montrent.

    Ce n'est pas une simple redite des nombres : l'interprétation dit
    où concentrer les efforts (ciblage, relances, canaux).
    """
    phrases = []
    if stats["total"] == 0:
        return ("Aucune candidature enregistrée pour le moment : le rapport "
                "prendra sens dès les premiers envois.")
    phrases.append(
        f"{stats['total']} candidatures envoyées, dont "
        f"{stats['avec_reponse']} ont reçu une réponse "
        f"({stats['taux_reponse']} %)."
    )
    if stats["taux_reponse"] < 30:
        phrases.append(
            "Le taux de réponse est faible : mieux vaut cibler des offres "
            "plus proches du profil et personnaliser chaque candidature "
            "plutôt que d'augmenter le volume."
        )
    elif stats["taux_reponse"] >= 50:
        phrases.append(
            "Le taux de réponse est bon : le ciblage actuel fonctionne, "
            "il vaut le coup de continuer sur les mêmes types d'offres."
        )
    else:
        phrases.append(
            "Le taux de réponse est correct : les relances peuvent encore "
            "le faire progresser, surtout sur les candidatures anciennes."
        )
    if stats["delai_moyen_jours"] is not None:
        phrases.append(
            f"Les entreprises répondent en moyenne sous "
            f"{stats['delai_moyen_jours']} jours : au-delà de ce délai, "
            "une relance polie est justifiée."
        )
    if stats["par_canal"]:
        meilleur = max(stats["par_canal"], key=stats["par_canal"].get)
        phrases.append(
            f"Le canal le plus utilisé est « {meilleur} » "
            f"({stats['par_canal'][meilleur]} envois) : c'est là que "
            "l'effort est le plus rentable pour l'instant."
        )
    return " ".join(phrases)


def generer_rapport(connexion, chemin_sortie="rapport.html"):
    """Écrit le rapport HTML et renvoie son chemin."""
    stats = calculer(connexion)

    par_statut = [
        (LIBELLES_STATUTS[s], stats["par_statut"][s]) for s in STATUTS
    ]
    par_canal = sorted(stats["par_canal"].items())

    delai = (
        f"{stats['delai_moyen_jours']} jours"
        if stats["delai_moyen_jours"] is not None
        else "pas encore de réponse enregistrée"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8">
<title>Rapport de suivi des candidatures</title>
<style>
body {{ font-family: sans-serif; max-width: 720px; margin: 2em auto; padding: 0 1em; }}
.kpi {{ display: flex; gap: 1em; flex-wrap: wrap; }}
.carte {{ border: 1px solid #ccc; border-radius: 8px; padding: 1em; min-width: 140px; }}
.carte b {{ font-size: 1.6em; color: #0f766e; }}
</style></head>
<body>
<h1>Suivi des candidatures</h1>
<div class="kpi">
<div class="carte"><b>{stats['total']}</b><br>candidatures</div>
<div class="carte"><b>{stats['taux_reponse']} %</b><br>taux de réponse</div>
<div class="carte"><b>{stats['taux_entretien']} %</b><br>d'entretiens (parmi les réponses)</div>
<div class="carte"><b>{delai}</b><br>délai moyen de réponse</div>
</div>
<h2>Répartition par statut</h2>
{_barres_svg(par_statut)}
<h2>Répartition par canal</h2>
{_barres_svg(par_canal) if par_canal else "<p>Aucune donnée.</p>"}
<h2>Ce que les chiffres montrent</h2>
<p>{escape(interpreter(stats))}</p>
</body></html>
"""
    with open(chemin_sortie, "w", encoding="utf-8") as fichier:
        fichier.write(html)
    return chemin_sortie
