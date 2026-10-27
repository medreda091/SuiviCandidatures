"""Accès à la base SQLite et définition du schéma.

Une candidature, c'est une ligne : une entreprise, un poste, une date
d'envoi, un statut et, quand elle arrive, une date de réponse. Tout le
reste (statistiques, relances, rapport) se calcule à partir de ces
quelques colonnes, ce qui garde les données propres et vérifiables.
"""

import sqlite3
from pathlib import Path

# Les seuls statuts acceptés : tout le reste est refusé à l'insertion,
# pour éviter les fautes de frappe qui faussent les statistiques.
STATUTS = (
    "envoyee",
    "en_attente",
    "entretien",
    "refusee",
    "acceptee",
)

# Libellés affichés dans les rapports (les valeurs stockées restent simples).
LIBELLES_STATUTS = {
    "envoyee": "Envoyée",
    "en_attente": "En attente de réponse",
    "entretien": "Entretien en cours",
    "refusee": "Refusée",
    "acceptee": "Acceptée",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS candidatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise TEXT NOT NULL,
    poste TEXT NOT NULL,
    canal TEXT NOT NULL DEFAULT 'site emploi',
    date_envoi TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'envoyee'
        CHECK (statut IN ('envoyee', 'en_attente', 'entretien', 'refusee', 'acceptee')),
    date_reponse TEXT,
    relance_le TEXT,
    notes TEXT DEFAULT ''
);
"""


def connecter(chemin="candidatures.db"):
    """Ouvre la base (la crée si besoin) et applique le schéma."""
    connexion = sqlite3.connect(chemin)
    connexion.row_factory = sqlite3.Row
    connexion.executescript(SCHEMA)
    connexion.commit()
    return connexion


def ajouter(connexion, entreprise, poste, date_envoi, canal="site emploi",
            statut="envoyee", notes=""):
    """Ajoute une candidature et renvoie son identifiant.

    Les champs vides et les statuts inconnus sont refusés : une ligne
    incomplète fausserait les indicateurs calculés ensuite.
    """
    entreprise = entreprise.strip()
    poste = poste.strip()
    if not entreprise or not poste or not date_envoi:
        raise ValueError("entreprise, poste et date_envoi sont obligatoires")
    if statut not in STATUTS:
        raise ValueError(f"statut inconnu : {statut}")
    curseur = connexion.execute(
        "INSERT INTO candidatures (entreprise, poste, canal, date_envoi,"
        " statut, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (entreprise, poste, canal.strip() or "site emploi", date_envoi,
         statut, notes.strip()),
    )
    connexion.commit()
    return curseur.lastrowid


def lister(connexion, statut=None):
    """Renvoie les candidatures, les plus récentes d'abord."""
    if statut:
        lignes = connexion.execute(
            "SELECT * FROM candidatures WHERE statut = ?"
            " ORDER BY date_envoi DESC, id DESC",
            (statut,),
        ).fetchall()
    else:
        lignes = connexion.execute(
            "SELECT * FROM candidatures ORDER BY date_envoi DESC, id DESC"
        ).fetchall()
    return [dict(ligne) for ligne in lignes]


def changer_statut(connexion, identifiant, statut, date_reponse=None):
    """Change le statut d'une candidature, et note la réponse si donnée."""
    if statut not in STATUTS:
        raise ValueError(f"statut inconnu : {statut}")
    curseur = connexion.execute(
        "UPDATE candidatures SET statut = ?, date_reponse = COALESCE(?, date_reponse)"
        " WHERE id = ?",
        (statut, date_reponse, identifiant),
    )
    connexion.commit()
    if curseur.rowcount == 0:
        raise LookupError(f"aucune candidature avec l'id {identifiant}")


def noter_relance(connexion, identifiant, date_relance):
    """Programme (ou met à jour) la date de relance d'une candidature."""
    curseur = connexion.execute(
        "UPDATE candidatures SET relance_le = ? WHERE id = ?",
        (date_relance, identifiant),
    )
    connexion.commit()
    if curseur.rowcount == 0:
        raise LookupError(f"aucune candidature avec l'id {identifiant}")


def chemin_par_defaut():
    """Chemin de la base utilisée par la ligne de commande."""
    return str(Path("candidatures.db"))
