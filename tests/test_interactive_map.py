"""Tests de préparation des données de la carte interactive."""

import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

import ui.maps.interactive_map as module_carte
import ui.zone_synthese_frame as module_synthese
from ui.maps.interactive_map import (
    CarteInteractive,
    PointCarte,
    calculer_emprise,
    calculer_echelle_k,
    couleur_k,
    formater_k_carte,
    graduations_k,
    normaliser_k,
    normaliser_points,
)
from ui.zone_synthese_frame import ZoneSyntheseFrame


class FauxVariable:
    def __init__(self, value=""):
        self.valeur = value

    def set(self, valeur):
        self.valeur = valeur

    def get(self):
        return self.valeur


class FauxWidget:
    def __init__(self, *args, **kwargs):
        self.options = kwargs
        self.place_visible = False

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def cget(self, cle):
        return self.options.get(cle)

    def pack(self, *args, **kwargs):
        return None

    def place(self, *args, **kwargs):
        self.place_visible = True

    def place_forget(self):
        self.place_visible = False

    def lift(self):
        return None


class FauxCanvas(FauxWidget):
    def bind(self, *args, **kwargs):
        return None

    def delete(self, *args, **kwargs):
        return None

    def winfo_width(self):
        return self.options.get("width", 112)

    def winfo_height(self):
        return 320

    def create_text(self, *args, **kwargs):
        return None

    def create_rectangle(self, *args, **kwargs):
        return None

    def create_line(self, *args, **kwargs):
        return None


class FauxMarqueur:
    def __init__(self, latitude, longitude, text, command, **kwargs):
        self.position = (latitude, longitude)
        self.text = text
        self.command = command
        self.options = kwargs
        self.data = None
        self.supprime = False

    def delete(self):
        self.supprime = True


class FausseCarte:
    def __init__(self, *args, **kwargs):
        self.marqueurs = []
        self.emprise = None
        self.serveur = None
        self.detruite = False
        self.running = True
        self.pre_cache_position = (1, 1)
        self.pre_cache_thread = None
        self.image_load_thread_pool = []
        self.image_load_queue_tasks = ["tuile"]
        self.image_load_queue_results = ["image"]

    def set_tile_server(self, serveur, max_zoom=19):
        self.serveur = (serveur, max_zoom)

    def pack(self, *args, **kwargs):
        return None

    def set_marker(self, latitude, longitude, text=None, command=None, **kwargs):
        marqueur = FauxMarqueur(
            latitude, longitude, text, command, **kwargs,
        )
        self.marqueurs.append(marqueur)
        return marqueur

    def fit_bounding_box(self, *emprise):
        self.emprise = emprise

    def destroy(self):
        self.detruite = True


class InteractiveMapTest(unittest.TestCase):

    def _creer_carte_simulee(self):
        with (
            patch.object(module_carte.tk.Frame, "__init__", return_value=None),
            patch.object(CarteInteractive, "pack_propagate"),
            patch.object(CarteInteractive, "after_idle", side_effect=lambda f: f()),
            patch.object(CarteInteractive, "_verifier_acces_tuiles"),
            patch.object(module_carte.tk, "StringVar", FauxVariable),
            patch.object(module_carte.tk, "Label", FauxWidget),
            patch.object(module_carte.tk, "Canvas", FauxCanvas),
            patch.object(module_carte, "TkinterMapView", FausseCarte),
        ):
            carte = CarteInteractive(Mock(), hauteur=320)
        carte.after_idle = lambda fonction: fonction()
        return carte

    def test_widget_cree_la_carte_openstreetmap(self):
        carte = self._creer_carte_simulee()
        self.assertIsInstance(carte._carte, FausseCarte)
        self.assertEqual(carte._carte.serveur[0], module_carte.URL_TUILES_OSM)

    def test_marqueurs_rafraichis_et_emprise_appliquee(self):
        carte = self._creer_carte_simulee()
        points = [
            PointCarte("P1", 45.0, 2.0, "radier", 1e-5),
            PointCarte("P2", 46.0, 3.0, "mouille", 2e-5),
        ]
        carte.actualiser(points)
        anciens = list(carte._marqueurs)
        self.assertEqual(len(anciens), 2)
        self.assertEqual(carte._carte.emprise, calculer_emprise(
            normaliser_points(points)
        ))

        carte.actualiser([points[1]])
        self.assertTrue(all(marqueur.supprime for marqueur in anciens))
        self.assertEqual(len(carte._marqueurs), 1)

    def test_widget_sans_point_affiche_un_message(self):
        carte = self._creer_carte_simulee()
        carte.actualiser([])
        self.assertIn("Aucun point GPS", carte._message.cget("text"))
        self.assertTrue(carte._message.place_visible)

    def test_fermeture_supprime_marqueurs_et_carte_sans_crash(self):
        carte = self._creer_carte_simulee()
        carte.actualiser([PointCarte("P1", 45.0, 2.0)])
        marqueur = carte._marqueurs[0]
        fausse_carte = carte._carte

        with patch.object(module_carte.tk.Frame, "destroy") as detruire_frame:
            carte.destroy()

        self.assertTrue(marqueur.supprime)
        self.assertTrue(fausse_carte.detruite)
        self.assertEqual(carte._marqueurs, [])
        self.assertIsNone(carte._carte)
        self.assertTrue(carte._detruit)
        detruire_frame.assert_called_once_with()

    def test_fermeture_annule_les_callbacks_et_neutralise_les_tuiles(self):
        carte = self._creer_carte_simulee()
        fausse_carte = carte._carte
        carte._rappel_reseau = "reseau"
        carte._rappel_ajustement = "ajustement"
        carte.after_cancel = Mock()

        carte.nettoyer_avant_fermeture()

        self.assertEqual(
            carte.after_cancel.call_args_list,
            [call("reseau"), call("ajustement")],
        )
        self.assertFalse(fausse_carte.running)
        self.assertEqual(fausse_carte.pre_cache_position, (1, 1))
        self.assertEqual(fausse_carte.image_load_queue_tasks, [])
        self.assertEqual(fausse_carte.image_load_queue_results, [])
        self.assertIsNone(carte._carte)

    def test_double_fermeture_et_destroy_sont_idempotents(self):
        carte = self._creer_carte_simulee()
        carte.after_cancel = Mock()
        with patch.object(module_carte.tk.Frame, "destroy") as detruire_frame:
            carte.nettoyer_avant_fermeture()
            carte.nettoyer_avant_fermeture()
            carte.destroy()
            carte.destroy()
        detruire_frame.assert_called_once_with()

    def test_rappels_internes_tkintermapview_sont_annules(self):
        carte = self._creer_carte_simulee()
        fausse_carte = carte._carte
        fausse_carte._tclCommands = ["commande_carte"]
        fausse_carte.tk = Mock()
        fausse_carte.tk.call.side_effect = (
            lambda *args: ("rappel_carte", "rappel_externe")
            if args == ("after", "info")
            else (("commande_carte", "timer")
                  if args[-1] == "rappel_carte"
                  else ("commande_externe", "timer"))
        )
        fausse_carte.after_cancel = Mock()

        carte.nettoyer_avant_fermeture()

        fausse_carte.after_cancel.assert_called_once_with("rappel_carte")

    def test_aucun_callback_ni_rafraichissement_apres_fermeture(self):
        carte = self._creer_carte_simulee()
        fausse_carte = carte._carte
        carte.nettoyer_avant_fermeture()

        carte.actualiser([PointCarte("P2", 46.0, 3.0)])
        carte._executer_ajustement(((47.0, 2.0), (45.0, 4.0)))
        carte._afficher_message("message tardif")
        carte._afficher_details(Mock())

        self.assertEqual(carte._marqueurs, [])
        self.assertIsNone(carte._carte)
        self.assertTrue(fausse_carte.detruite)

    def test_clic_marqueur_affiche_les_details(self):
        carte = self._creer_carte_simulee()
        carte.actualiser([
            PointCarte("P1", 45.0, 2.0, "radier", 1.2e-5)
        ])
        carte._afficher_details(carte._marqueurs[0])
        details = carte._details.get()
        for texte in ("P1", "45.000000", "2.000000", "radier", "1.200e-05 m/s"):
            self.assertIn(texte, details)

    def test_zone_synthese_ajoute_la_carte_en_pleine_largeur(self):
        fausse_carte = Mock()
        constructeur = Mock(return_value=fausse_carte)
        synthese = ZoneSyntheseFrame.__new__(ZoneSyntheseFrame)
        synthese.carte_interactive = None
        points = [PointCarte("P1", 45.0, 2.0)]

        with patch.object(module_synthese, "CarteInteractive", constructeur):
            synthese._ajouter_carte_interactive("conteneur", points)

        constructeur.assert_called_once_with("conteneur", hauteur=480)
        fausse_carte.pack.assert_called_once_with(fill="x", pady=(8, 24))
        fausse_carte.actualiser.assert_called_once_with(points)
        self.assertIs(synthese.carte_interactive, fausse_carte)

    def test_pdf_utilise_la_carte_openstreetmap(self):
        source_pdf = (
            Path(__file__).resolve().parents[1]
            / "services" / "pdf" / "charts.py"
        ).read_text(encoding="utf-8")
        source_zone = (
            Path(__file__).resolve().parents[1]
            / "ui" / "zone_synthese_frame.py"
        ).read_text(encoding="utf-8")
        self.assertIn("generer_carte_osm_png", source_pdf)
        self.assertIn("_generer_carte_pdf_png", source_pdf)
        self.assertNotIn("charts.graphique_carte_points", source_zone)

    def test_aucun_point(self):
        self.assertEqual(normaliser_points([]), [])
        self.assertIsNone(calculer_emprise([]))

    def test_un_point_produit_une_emprise_centree(self):
        valides = normaliser_points([PointCarte("P1", 45.0, 2.0)])
        haut_gauche, bas_droit = calculer_emprise(valides)
        self.assertGreater(haut_gauche[0], 45.0)
        self.assertLess(haut_gauche[1], 2.0)
        self.assertLess(bas_droit[0], 45.0)
        self.assertGreater(bas_droit[1], 2.0)

    def test_plusieurs_points_eloignes_restent_dans_emprise(self):
        valides = normaliser_points([
            PointCarte("Nord", 50.0, -4.0),
            PointCarte("Sud", 42.0, 8.0),
        ])
        haut_gauche, bas_droit = calculer_emprise(valides)
        self.assertGreater(haut_gauche[0], 50.0)
        self.assertLess(haut_gauche[1], -4.0)
        self.assertLess(bas_droit[0], 42.0)
        self.assertGreater(bas_droit[1], 8.0)

    def test_coordonnees_invalides_sont_ignorees(self):
        valides = normaliser_points([
            PointCarte("Texte", "invalide", 2.0),
            PointCarte("Latitude", 91.0, 2.0),
            PointCarte("Longitude", 45.0, 181.0),
            PointCarte("Valide", 45.0, 2.0),
        ])
        self.assertEqual([point.nom for point, _, _ in valides], ["Valide"])

    def test_precision_k_proches_et_normalisation_commune(self):
        points = normaliser_points([
            PointCarte("p1", 45.0, 2.0, k_moyen=0.0001808891385374027),
            PointCarte("p2", 45.1, 2.1, k_moyen=0.0001164385517563855),
            PointCarte("p3", 45.2, 2.2, k_moyen=0.0001808034393440735),
        ])
        valeurs, echelle = calculer_echelle_k(points)

        self.assertEqual(echelle, (valeurs[1], valeurs[0]))
        self.assertEqual(normaliser_k(valeurs[1], echelle), 0.0)
        self.assertEqual(normaliser_k(valeurs[0], echelle), 1.0)
        self.assertGreater(normaliser_k(valeurs[2], echelle), 0.99)
        self.assertNotEqual(
            couleur_k(valeurs[0], echelle), couleur_k(valeurs[2], echelle)
        )
        self.assertEqual(graduations_k(echelle)[0], echelle[0])
        self.assertEqual(graduations_k(echelle)[-1], echelle[1])
        self.assertIn("e-04", formater_k_carte(valeurs[1], echelle))

    def test_k_identiques_gardent_bornes_exactes_et_couleur_unique(self):
        points = normaliser_points([
            PointCarte("P1", 45.0, 2.0, k_moyen=1.23456789e-8),
            PointCarte("P2", 46.0, 3.0, k_moyen=1.23456789e-8),
        ])
        valeurs, echelle = calculer_echelle_k(points)

        self.assertEqual(echelle, (1.23456789e-8, 1.23456789e-8))
        self.assertEqual(normaliser_k(valeurs[0], echelle), 0.5)
        self.assertEqual(
            couleur_k(valeurs[0], echelle), couleur_k(valeurs[1], echelle)
        )
        self.assertEqual(graduations_k(echelle), [1.23456789e-8])


if __name__ == "__main__":
    unittest.main()
