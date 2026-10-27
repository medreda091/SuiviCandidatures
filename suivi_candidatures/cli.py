"""Ligne de commande : ajouter, lister, suivre, relancer, analyser.

Utilisation (depuis la racine du projet) :
    python main.py ajouter --entreprise ACME --poste "Data Analyst" --date 2026-10-01
    python main.py lister
    python main.py statut 3 entretien --reponse 2026-10-12
    python main.py relance 3 --le 2026-10-20
    python main.py stats
    python main.py relances
    python main.py rapport
"""

import argparse
import sys

from .base import (
    LIBELLES_STATUTS,
    STATUTS,
    ajouter,
    changer_statut,
    connecter,
    lister,
    noter_relance,
)
from .import_csv import importer
from .rapport import generer_rapport
from .statistiques import a_relancer_bientot, calculer, relances_en_retard


def _connexion(args):
    return connecter(args.base)


def _cmd_ajouter(args):
    connexion = _connexion(args)
    identifiant = ajouter(
        connexion, args.entreprise, args.poste, args.date,
        canal=args.canal, statut=args.statut, notes=args.notes,
    )
    print(f"Candidature n°{identifiant} ajoutée : {args.poste} chez {args.entreprise}.")
    connexion.close()


def _cmd_lister(args):
    connexion = _connexion(args)
    lignes = lister(connexion, statut=args.statut)
    connexion.close()
    if not lignes:
        print("Aucune candidature pour le moment.")
        return
    for ligne in lignes:
        reponse = f" (réponse le {ligne['date_reponse']})" if ligne["date_reponse"] else ""
        print(
            f"[{ligne['id']}] {ligne['entreprise']} — {ligne['poste']} | "
            f"{LIBELLES_STATUTS[ligne['statut']]} | envoyé le {ligne['date_envoi']}"
            f" | {ligne['canal']}{reponse}"
        )


def _cmd_statut(args):
    connexion = _connexion(args)
    changer_statut(connexion, args.id, args.statut, date_reponse=args.reponse)
    print(f"Candidature n°{args.id} passée en « {LIBELLES_STATUTS[args.statut]} ».")
    connexion.close()


def _cmd_relance(args):
    connexion = _connexion(args)
    noter_relance(connexion, args.id, args.le)
    print(f"Relance de la candidature n°{args.id} prévue le {args.le}.")
    connexion.close()


def _cmd_stats(args):
    connexion = _connexion(args)
    stats = calculer(connexion)
    connexion.close()
    print(f"Candidatures envoyées : {stats['total']}")
    for statut in STATUTS:
        print(f"  {LIBELLES_STATUTS[statut]} : {stats['par_statut'][statut]}")
    print(f"Taux de réponse : {stats['taux_reponse']} %")
    print(f"Taux d'entretien (parmi les réponses) : {stats['taux_entretien']} %")
    if stats["delai_moyen_jours"] is not None:
        print(f"Délai moyen de réponse : {stats['delai_moyen_jours']} jours")
    for canal, nombre in sorted(stats["par_canal"].items()):
        print(f"  via {canal} : {nombre}")


def _cmd_relances(args):
    connexion = _connexion(args)
    en_retard = relances_en_retard(connexion)
    oublis = a_relancer_bientot(connexion)
    connexion.close()
    if not en_retard and not oublis:
        print("Aucune relance à faire. Tout est à jour.")
        return
    for ligne in en_retard:
        print(f"EN RETARD : [{ligne['id']}] {ligne['entreprise']} — {ligne['poste']}"
              f" (relance prévue le {ligne['relance_le']})")
    for ligne in oublis:
        print(f"À RELANCER : [{ligne['id']}] {ligne['entreprise']} — {ligne['poste']}"
              f" (envoyée le {ligne['date_envoi']}, jamais relancée)")


def _cmd_importer(args):
    connexion = _connexion(args)
    nombre, erreurs = importer(connexion, args.fichier)
    connexion.close()
    print(f"{nombre} candidature(s) importée(s) depuis {args.fichier}.")
    if erreurs:
        print("Lignes ignorées (à corriger dans le fichier) :")
        for erreur in erreurs:
            print(f"  - {erreur}")


def _cmd_rapport(args):
    connexion = _connexion(args)
    chemin = generer_rapport(connexion, args.sortie)
    connexion.close()
    print(f"Rapport généré : {chemin}")


def construire_parser():
    """Définit toutes les sous-commandes de l'outil."""
    parser = argparse.ArgumentParser(
        prog="suivi-candidatures",
        description="Suivi de candidatures : statuts, relances et statistiques.",
    )
    parser.add_argument("--base", default="candidatures.db",
                        help="chemin de la base SQLite (défaut : candidatures.db)")
    sous = parser.add_subparsers(dest="commande", required=True)

    p = sous.add_parser("ajouter", help="ajouter une candidature")
    p.add_argument("--entreprise", required=True)
    p.add_argument("--poste", required=True)
    p.add_argument("--date", required=True, help="date d'envoi (AAAA-MM-JJ)")
    p.add_argument("--canal", default="site emploi")
    p.add_argument("--statut", default="envoyee", choices=STATUTS)
    p.add_argument("--notes", default="")
    p.set_defaults(fonction=_cmd_ajouter)

    p = sous.add_parser("lister", help="lister les candidatures")
    p.add_argument("--statut", choices=STATUTS, default=None)
    p.set_defaults(fonction=_cmd_lister)

    p = sous.add_parser("statut", help="changer le statut d'une candidature")
    p.add_argument("id", type=int)
    p.add_argument("statut", choices=STATUTS)
    p.add_argument("--reponse", default=None, help="date de la réponse (AAAA-MM-JJ)")
    p.set_defaults(fonction=_cmd_statut)

    p = sous.add_parser("relance", help="programmer une relance")
    p.add_argument("id", type=int)
    p.add_argument("--le", required=True, help="date de relance (AAAA-MM-JJ)")
    p.set_defaults(fonction=_cmd_relance)

    p = sous.add_parser("stats", help="afficher les statistiques")
    p.set_defaults(fonction=_cmd_stats)

    p = sous.add_parser("relances", help="voir les relances à faire")
    p.set_defaults(fonction=_cmd_relances)

    p = sous.add_parser("importer", help="importer un fichier CSV (avec rapport qualité)")
    p.add_argument("fichier")
    p.set_defaults(fonction=_cmd_importer)

    p = sous.add_parser("rapport", help="générer le rapport HTML avec graphiques")
    p.add_argument("--sortie", default="rapport.html")
    p.set_defaults(fonction=_cmd_rapport)

    return parser


def main(argv=None):
    """Point d'entrée de la ligne de commande."""
    args = construire_parser().parse_args(argv)
    try:
        args.fonction(args)
    except (ValueError, LookupError) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
