"""Tests de la base : ajout, liste, statuts, relances."""

import pytest

from suivi_candidatures.base import (
    ajouter,
    changer_statut,
    connecter,
    lister,
    noter_relance,
)


@pytest.fixture
def connexion():
    """Base vide en mémoire, fermée après chaque test."""
    connexion = connecter(":memory:")
    yield connexion
    connexion.close()


def test_ajouter_et_lister(connexion):
    identifiant = ajouter(connexion, "ACME", "Data Analyst", "2026-10-01")
    lignes = lister(connexion)
    assert len(lignes) == 1
    assert lignes[0]["id"] == identifiant
    assert lignes[0]["entreprise"] == "ACME"
    assert lignes[0]["statut"] == "envoyee"


def test_lister_trie_par_date_desc(connexion):
    ajouter(connexion, "A", "Poste 1", "2026-10-01")
    ajouter(connexion, "B", "Poste 2", "2026-10-05")
    lignes = lister(connexion)
    assert lignes[0]["entreprise"] == "B"
    assert lignes[1]["entreprise"] == "A"


def test_ajouter_refuse_les_champs_vides(connexion):
    with pytest.raises(ValueError):
        ajouter(connexion, "", "Data Analyst", "2026-10-01")
    with pytest.raises(ValueError):
        ajouter(connexion, "ACME", "Data Analyst", "")


def test_ajouter_refuse_un_statut_inconnu(connexion):
    with pytest.raises(ValueError):
        ajouter(connexion, "ACME", "Data Analyst", "2026-10-01",
                statut="peut-etre")


def test_changer_statut_avec_reponse(connexion):
    identifiant = ajouter(connexion, "ACME", "Data Analyst", "2026-10-01")
    changer_statut(connexion, identifiant, "entretien",
                   date_reponse="2026-10-08")
    ligne = lister(connexion)[0]
    assert ligne["statut"] == "entretien"
    assert ligne["date_reponse"] == "2026-10-08"


def test_changer_statut_d_un_id_inconnu(connexion):
    with pytest.raises(LookupError):
        changer_statut(connexion, 999, "refusee")


def test_noter_relance(connexion):
    identifiant = ajouter(connexion, "ACME", "Data Analyst", "2026-10-01")
    noter_relance(connexion, identifiant, "2026-10-15")
    assert lister(connexion)[0]["relance_le"] == "2026-10-15"
