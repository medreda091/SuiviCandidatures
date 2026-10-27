"""Calcul des indicateurs (KPI) à partir des candidatures.

Tous les indicateurs sont calculés à la demande, jamais stockés : les
chiffres affichés reflètent toujours l'état réel de la base.
"""

from datetime import date

from .base import STATUTS, lister


def _jours_entre(debut, fin):
    """Nombre de jours entre deux dates ISO (None si une date manque)."""
    if not debut or not fin:
        return None
    debut = date.fromisoformat(debut)
    fin = date.fromisoformat(fin)
    return (fin - debut).days


def calculer(connexion):
    """Renvoie le dictionnaire complet des indicateurs."""
    candidatures = lister(connexion)
    total = len(candidatures)

    par_statut = {statut: 0 for statut in STATUTS}
    for candidature in candidatures:
        par_statut[candidature["statut"]] += 1

    # Une candidature "a eu une réponse" dès qu'elle est passée en
    # entretien, refusée ou acceptée : c'est ce taux-là qui dit si
    # les candidatures ciblent les bonnes offres.
    avec_reponse = sum(
        par_statut[s] for s in ("entretien", "refusee", "acceptee")
    )
    taux_reponse = round(100 * avec_reponse / total, 1) if total else 0.0

    # Délai moyen entre l'envoi et la première réponse enregistrée.
    delais = [
        _jours_entre(c["date_envoi"], c["date_reponse"])
        for c in candidatures
        if c["date_reponse"]
    ]
    delais = [d for d in delais if d is not None]
    delai_moyen = round(sum(delais) / len(delais), 1) if delais else None

    # Répartition par canal : utile pour savoir où concentrer les efforts.
    par_canal = {}
    for candidature in candidatures:
        canal = candidature["canal"] or "inconnu"
        par_canal[canal] = par_canal.get(canal, 0) + 1

    # Taux d'entretiens parmi les candidatures ayant eu une réponse.
    taux_entretien = (
        round(100 * par_statut["entretien"] / avec_reponse, 1)
        if avec_reponse
        else 0.0
    )

    return {
        "total": total,
        "par_statut": par_statut,
        "avec_reponse": avec_reponse,
        "taux_reponse": taux_reponse,
        "taux_entretien": taux_entretien,
        "delai_moyen_jours": delai_moyen,
        "par_canal": par_canal,
    }


def relances_en_retard(connexion, aujourd_hui=None):
    """Candidatures dont la relance prévue est passée sans réponse.

    Une candidature déjà refusée ou acceptée ne doit plus être relancée.
    """
    aujourd_hui = aujourd_hui or date.today().isoformat()
    en_retard = []
    for candidature in lister(connexion):
        if candidature["statut"] in ("refusee", "acceptee"):
            continue
        relance = candidature["relance_le"]
        if relance and relance < aujourd_hui:
            en_retard.append(candidature)
    return en_retard


def a_relancer_bientot(connexion, aujourd_hui=None, jours=7):
    """Candidatures sans relance prévue, envoyées depuis plus de 10 jours.

    Ce sont les oublis classiques : une candidature envoyée puis jamais
    relancée. Le seuil de 10 jours laisse le temps à l'entreprise de
    répondre avant de relancer.
    """
    aujourd_hui = date.fromisoformat(aujourd_hui or date.today().isoformat())
    oublis = []
    for candidature in lister(connexion):
        if candidature["statut"] in ("refusee", "acceptee"):
            continue
        if candidature["relance_le"]:
            continue
        envoye_le = date.fromisoformat(candidature["date_envoi"])
        if (aujourd_hui - envoye_le).days >= 10:
            oublis.append(candidature)
    return oublis
