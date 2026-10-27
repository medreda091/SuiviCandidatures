"""Import d'un fichier CSV et contrôle qualité des données.

Le CSV attendu a les colonnes : entreprise, poste, canal, date_envoi,
statut, date_reponse, notes. Les lignes incomplètes ou au statut
inconnu ne sont pas importées : elles sont listées dans un rapport
de qualité, pour que l'utilisateur corrige son fichier au lieu
d'importer des données fausses en silence.
"""

import csv

from .base import STATUTS, ajouter


def importer(connexion, chemin_csv):
    """Importe le fichier et renvoie (nombre importé, liste d'erreurs).

    Chaque erreur indique le numéro de ligne et le problème rencontré.
    """
    importees = 0
    erreurs = []
    with open(chemin_csv, newline="", encoding="utf-8") as fichier:
        lecteur = csv.DictReader(fichier)
        for numero, ligne in enumerate(lecteur, start=2):
            entreprise = (ligne.get("entreprise") or "").strip()
            poste = (ligne.get("poste") or "").strip()
            date_envoi = (ligne.get("date_envoi") or "").strip()
            statut = (ligne.get("statut") or "envoyee").strip() or "envoyee"
            if not entreprise or not poste or not date_envoi:
                erreurs.append(
                    f"ligne {numero} : entreprise, poste ou date_envoi manquant"
                )
                continue
            if statut not in STATUTS:
                erreurs.append(f"ligne {numero} : statut inconnu « {statut} »")
                continue
            try:
                ajouter(
                    connexion, entreprise, poste, date_envoi,
                    canal=(ligne.get("canal") or "site emploi"),
                    statut=statut,
                    notes=(ligne.get("notes") or ""),
                )
            except ValueError as erreur:
                erreurs.append(f"ligne {numero} : {erreur}")
                continue
            importees += 1
            # Si une date de réponse est fournie, on l'enregistre.
            date_reponse = (ligne.get("date_reponse") or "").strip()
            if date_reponse:
                connexion.execute(
                    "UPDATE candidatures SET date_reponse = ?"
                    " WHERE entreprise = ? AND poste = ? AND date_envoi = ?",
                    (date_reponse, entreprise, poste, date_envoi),
                )
                connexion.commit()
    return importees, erreurs
