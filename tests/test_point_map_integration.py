"""Tests de l'intégration de la carte dans la liste des points."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import ui.point_frame as module_points
from ui.maps import PointCarte
from ui.maps.interactive_map import normaliser_points
from ui.point_frame import PointFrame


class FausseTable:
    def __init__(self):
        self.lignes = ["ancienne"]

    def get_children(self):
        return tuple(self.lignes)

    def delete(self, ligne):
        self.lignes.remove(ligne)


class PointMapIntegrationTest(unittest.TestCase):

    @staticmethod
    def _point(numero, zone_id=1, latitude=45.0, longitude=2.0):
        return SimpleNamespace(
            id=numero,
            zone_id=zone_id,
            nom=f"P{numero}",
            latitude=latitude,
            longitude=longitude,
            facies="radier",
        )

    def _creer_frame(self, points=None, zone_id=1):
        frame = PointFrame.__new__(PointFrame)
        frame.zone_id = zone_id
        frame.table = FausseTable()
        frame.carte_interactive = Mock()
        frame.point_repo = Mock()
        frame.point_repo.lister_par_zone.return_value = list(points or [])
        frame.repetition_repo = Mock()
        frame.repetition_repo.compter_par_point.return_value = 2
        frame.repetition_repo.moyenne_k_par_point.return_value = 1.2e-5
        frame.repetition_repo.profondeurs_par_point.return_value = "0.1"
        return frame

    def test_creation_d_une_seule_instance_de_carte(self):
        frame = PointFrame.__new__(PointFrame)
        frame.carte_interactive = None
        fausse_carte = Mock()
        with (
            patch.object(module_points.tk, "Label", return_value=Mock()),
            patch.object(module_points, "CarteInteractive", return_value=fausse_carte) as constructeur,
        ):
            frame._creer_carte_interactive("conteneur")
            frame._creer_carte_interactive("conteneur")

        constructeur.assert_called_once_with("conteneur", hauteur=440)
        fausse_carte.pack.assert_called_once_with(fill="x", pady=(8, 24))

    def test_transmet_les_points_et_le_k_deja_charge_de_l_etude_courante(self):
        points = [self._point(1), self._point(2)]
        frame = self._creer_frame(points, zone_id=7)

        with patch.object(module_points, "inserer_ligne"):
            frame.charger_points()

        frame.point_repo.lister_par_zone.assert_called_once_with(7)
        transmis = frame.carte_interactive.actualiser.call_args.args[0]
        self.assertEqual([point.nom for point in transmis], ["P1", "P2"])
        self.assertTrue(all(isinstance(point, PointCarte) for point in transmis))
        self.assertTrue(all(point.k_moyen == 1.2e-5 for point in transmis))

    def test_rafraichissement_apres_ajout(self):
        frame = self._creer_frame([self._point(1)])
        with patch.object(module_points, "PointDialog") as dialogue:
            frame._ouvrir_creation()
        rappel = dialogue.call_args.kwargs["refresh_callback"]
        frame.point_repo.lister_par_zone.return_value.append(self._point(2))
        with patch.object(module_points, "inserer_ligne"):
            rappel()
        self.assertEqual(len(frame.carte_interactive.actualiser.call_args.args[0]), 2)

    def test_rafraichissement_apres_modification(self):
        frame = self._creer_frame([self._point(1)])
        frame._selection = Mock(return_value=(1, "P1"))
        frame.point_repo.trouver_par_id.return_value = self._point(1)
        with patch.object(module_points, "PointDialog") as dialogue:
            frame._modifier()
        rappel = dialogue.call_args.kwargs["refresh_callback"]
        frame.point_repo.lister_par_zone.return_value[0].latitude = 46.0
        with patch.object(module_points, "inserer_ligne"):
            rappel()
        transmis = frame.carte_interactive.actualiser.call_args.args[0]
        self.assertEqual(transmis[0].latitude, 46.0)

    def test_rafraichissement_apres_suppression(self):
        frame = self._creer_frame([self._point(1)])
        frame._selection = Mock(return_value=(1, "P1"))
        frame.point_repo.supprimer.side_effect = lambda _pid: (
            frame.point_repo.lister_par_zone.return_value.clear()
        )
        with (
            patch.object(module_points.messagebox, "askyesno", return_value=True),
            patch.object(module_points, "inserer_ligne"),
        ):
            frame._supprimer()
        frame.point_repo.supprimer.assert_called_once_with(1)
        frame.carte_interactive.actualiser.assert_called_once_with([])

    def test_rechargement_ne_duplique_pas_les_points(self):
        frame = self._creer_frame([self._point(1)])
        with patch.object(module_points, "inserer_ligne"):
            frame.charger_points()
            frame.charger_points()
        self.assertEqual(frame.carte_interactive.actualiser.call_count, 2)
        self.assertEqual(len(frame.carte_interactive.actualiser.call_args.args[0]), 1)

    def test_changement_d_etude_utilise_uniquement_le_nouvel_identifiant(self):
        frame = self._creer_frame([self._point(8, zone_id=2)], zone_id=2)
        with patch.object(module_points, "inserer_ligne"):
            frame.charger_points()
        frame.point_repo.lister_par_zone.assert_called_once_with(2)
        transmis = frame.carte_interactive.actualiser.call_args.args[0]
        self.assertEqual([point.nom for point in transmis], ["P8"])

    def test_point_sans_coordonnees_reste_transmis_puis_est_ignore_par_la_carte(self):
        frame = self._creer_frame([self._point(1, latitude=None, longitude=None)])
        with patch.object(module_points, "inserer_ligne"):
            frame.charger_points()
        transmis = frame.carte_interactive.actualiser.call_args.args[0]
        self.assertEqual(len(transmis), 1)
        self.assertEqual(normaliser_points(transmis), [])

    def test_etude_vide_actualise_la_carte_avec_une_liste_vide(self):
        frame = self._creer_frame([])
        with patch.object(module_points, "inserer_ligne"):
            frame.charger_points()
        frame.carte_interactive.actualiser.assert_called_once_with([])


if __name__ == "__main__":
    unittest.main()
