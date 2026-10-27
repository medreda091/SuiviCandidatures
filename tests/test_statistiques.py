"""Tests des statistiques, des relances et de l'import CSV."""

from suivi_candidatures.base import (
    ajouter,
    changer_statut,
    connecter,
    noter_relance,
)
from suivi_candidatures.import_csv import importer
from suivi_candidatures.statistiques import (
    a_relancer_bientot,
    calculer,
    relances_en_retard,
)


def _base_exemple():
    connexion = connecter(":memory:")
    identifiant_a = ajouter(connexion, "A", "Data Analyst", "2026-10-01")
    changer_statut(connexion, identifiant_a, "entretien",
                   date_reponse="2026-10-08")
    identifiant_b = ajouter(connexion, "B", "Business Analyst", "2026-10-02")
    changer_statut(connexion, identifiant_b, "refusee",
                   date_reponse="2026-10-12")
    ajouter(connexion, "C", "Analyste BI", "2026-10-03")
    ajouter(connexion, "D", "Chef de projet", "2026-10-04")
    return connexion


def test_statistiques_completes():
    stats = calculer(_base_exemple())
    assert stats["total"] == 4
    assert stats["par_statut"]["entretien"] == 1
    assert stats["par_statut"]["refusee"] == 1
    assert stats["avec_reponse"] == 2
    assert stats["taux_reponse"] == 50.0
    assert stats["taux_entretien"] == 50.0
    # Délais : 7 et 10 jours, moyenne 8,5.
    assert stats["delai_moyen_jours"] == 8.5


def test_statistiques_base_vide():
    stats = calculer(connecter(":memory:"))
    assert stats["total"] == 0
    assert stats["taux_reponse"] == 0.0
    assert stats["delai_moyen_jours"] is None


def test_relances_en_retard():
    connexion = _base_exemple()
    identifiant = ajouter(connexion, "E", "Consultant", "2026-09-20")
    noter_relance(connexion, identifiant, "2026-10-01")
    en_retard = relances_en_retard(connexion, aujourd_hui="2026-10-27")
    assert [ligne["entreprise"] for ligne in en_retard] == ["E"]


def test_relances_ignorent_les_dossiers_clos():
    connexion = _base_exemple()
    # B est refusée : même avec une relance passée, elle ne ressort pas.
    noter_relance(connexion, 2, "2026-10-01")
    en_retard = relances_en_retard(connexion, aujourd_hui="2026-10-27")
    assert all(ligne["entreprise"] != "B" for ligne in en_retard)


def test_candidatures_oubliees_sans_relance():
    connexion = _base_exemple()
    oublis = a_relancer_bientot(connexion, aujourd_hui="2026-10-27")
    # C et D envoyées depuis plus de 10 jours, jamais relancées.
    assert {ligne["entreprise"] for ligne in oublis} == {"C", "D"}


def test_import_csv_avec_lignes_en_erreur(tmp_path):
    fichier = tmp_path / "test.csv"
    fichier.write_text(
        "entreprise,poste,canal,date_envoi,statut,date_reponse,notes\n"
        "ACME,Data Analyst,LinkedIn,2026-10-01,envoyee,,\n"
        ",Poste sans entreprise,LinkedIn,2026-10-01,envoyee,,\n"
        "AUTRE,Poste X,site emploi,2026-10-02,statut-bizarre,,\n",
        encoding="utf-8",
    )
    connexion = connecter(":memory:")
    nombre, erreurs = importer(connexion, str(fichier))
    assert nombre == 1
    assert len(erreurs) == 2
    assert any("ligne 3" in e for e in erreurs)
    assert any("ligne 4" in e for e in erreurs)


def test_import_csv_enregistre_la_reponse():
    import tempfile
    import os

    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                     encoding="utf-8") as f:
        f.write("entreprise,poste,canal,date_envoi,statut,date_reponse,notes\n"
                "ACME,Data Analyst,LinkedIn,2026-10-01,entretien,2026-10-08,\n")
        chemin = f.name
    try:
        connexion = connecter(":memory:")
        nombre, erreurs = importer(connexion, chemin)
        assert nombre == 1
        assert erreurs == []
        from suivi_candidatures.base import lister
        assert lister(connexion)[0]["date_reponse"] == "2026-10-08"
    finally:
        os.unlink(chemin)
