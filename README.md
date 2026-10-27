# SuiviCandidatures

Un outil en ligne de commande pour suivre ses candidatures : statuts,
relances, statistiques et rapport avec graphiques. Il est pensé pour
une recherche d'alternance ou d'emploi : on y voit d'un coup d'œil où
en sont les candidatures, lesquelles relancer, et ce que les chiffres
racontent vraiment.

## Ce que l'outil fait

- **Suivre** chaque candidature : entreprise, poste, canal, date
  d'envoi, statut (envoyée, en attente, entretien, refusée, acceptée).
- **Relancer au bon moment** : relances en retard et candidatures
  envoyées depuis plus de 10 jours sans relance, jamais relancées
  quand le dossier est clos ou en entretien.
- **Mesurer** avec des indicateurs clairs :
  - nombre de candidatures envoyées ;
  - **taux de réponse** (part des candidatures ayant reçu une réponse) ;
  - **taux d'entretien** parmi les candidatures ayant eu une réponse ;
  - **délai moyen de réponse** en jours ;
  - répartition par statut et par canal (LinkedIn, site emploi,
    email recruteur…).
- **Importer** un fichier CSV existant, avec un rapport qualité : les
  lignes incomplètes ou au statut inconnu sont signalées, pas
  importées en silence.
- **Générer un rapport HTML** avec graphiques (SVG, sans dépendance)
  et une interprétation écrite des résultats.

## Ce que les chiffres montrent (exemple)

Avec les données d'exemple fournies (`donnees_exemple.csv`) :

- 6 candidatures, 50 % de taux de réponse, 66,7 % d'entretiens parmi
  les réponses, délai moyen de 9,3 jours.
- **Interprétation :** le taux de réponse est correct et la
  transformation en entretien est bonne — le ciblage fonctionne. Les
  3 candidatures envoyées début octobre sans relance sont le premier
  levier : une relance polie au-delà du délai moyen de réponse peut
  encore faire progresser le taux de réponse, sans envoyer plus de
  candidatures.

C'est le point important de l'outil : il ne se contente pas
d'afficher des graphiques, il dit où concentrer l'effort — ciblage,
relances ou canaux — à partir des chiffres réels.

## Stack

- Python 3.12 (bibliothèque standard uniquement pour l'application)
- SQLite (base locale, un seul fichier)
- pytest pour les tests
- Docker et GitHub Actions pour les tests automatiques

## Installation

```bash
git clone https://github.com/medreda091/SuiviCandidatures.git
cd SuiviCandidatures
python3 -m pytest -q   # vérifie que tout fonctionne
```

Aucune dépendance à installer pour utiliser l'outil lui-même ; seul
pytest est nécessaire pour les tests (`pip install -r requirements.txt`).

## Utilisation

```bash
# Ajouter une candidature
python main.py ajouter --entreprise ACME --poste "Data Analyst" --date 2026-10-01 --canal LinkedIn

# Lister les candidatures (éventuellement filtrées par statut)
python main.py lister
python main.py lister --statut entretien

# Changer de statut, en notant la date de réponse
python main.py statut 3 entretien --reponse 2026-10-12

# Programmer une relance
python main.py relance 3 --le 2026-10-20

# Voir les statistiques
python main.py stats

# Voir les relances à faire
python main.py relances

# Importer un CSV existant (rapport qualité inclus)
python main.py importer donnees_exemple.csv

# Générer le rapport HTML avec graphiques
python main.py rapport
```

La base par défaut est le fichier `candidatures.db` dans le dossier
courant ; on peut en choisir un autre avec `--base` avant la commande
(`python main.py --base suivi.db lister`).

### Format du CSV à importer

```csv
entreprise,poste,canal,date_envoi,statut,date_reponse,notes
ACME,Data Analyst,LinkedIn,2026-10-01,envoyee,,
```

Les colonnes `date_reponse` et `notes` peuvent être vides. Les lignes
avec un champ obligatoire manquant ou un statut inconnu sont ignorées
et listées à la fin de l'import.

## Structure du projet

```
SuiviCandidatures/
├── main.py                        # point d'entrée
├── donnees_exemple.csv            # jeu de données d'exemple
├── suivi_candidatures/
│   ├── base.py                    # schéma SQLite, ajout, statuts, relances
│   ├── statistiques.py            # KPI, relances en retard, oublis
│   ├── import_csv.py              # import CSV avec contrôle qualité
│   ├── rapport.py                 # rapport HTML, graphiques SVG, interprétation
│   └── cli.py                     # ligne de commande
└── tests/
    ├── test_base.py
    └── test_statistiques.py
```

## Qualité des données

- Les statuts possibles sont limités à une liste fixe : une faute de
  frappe ne peut pas créer un statut fantôme qui fausserait les
  statistiques.
- Les champs obligatoires (entreprise, poste, date d'envoi) sont
  vérifiés à l'ajout comme à l'import.
- Les indicateurs sont calculés à la demande à partir de la base,
  jamais stockés : les chiffres affichés reflètent toujours l'état réel.

## Tests

```bash
python3 -m pytest -q
```

14 tests : ajout et statuts, tri, refus des données invalides,
calcul des KPI (taux de réponse, délai moyen), relances en retard,
oublis sans relance, import CSV avec lignes en erreur.

## Licence

MIT — voir le fichier `LICENSE`.
