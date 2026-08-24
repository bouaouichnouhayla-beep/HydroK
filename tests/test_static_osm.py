"""Tests du rendu OpenStreetMap statique destiné au PDF."""

import io
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from ui.maps import PointCarte
from ui.maps.interactive_map import normaliser_points
from ui.maps.static_osm import (
    _coordonnees_monde,
    calculer_vue_osm,
    generer_carte_osm_png,
)
from services.pdf.charts import PdfChartsMixin


class StaticOsmTest(unittest.TestCase):

    def setUp(self):
        self.points = [
            PointCarte("P1", 45.1236, 4.7895),
            PointCarte("P2", 45.8055848, 4.9158112),
            PointCarte("P3", 45.8028186, 4.8916378),
        ]

    def test_vue_contient_tous_les_points_valides(self):
        largeur, hauteur = 900, 380
        valides = normaliser_points(self.points)
        centre_x, centre_y, zoom = calculer_vue_osm(
            valides, largeur, hauteur
        )
        for _, latitude, longitude in valides:
            x, y = _coordonnees_monde(latitude, longitude, zoom)
            self.assertGreaterEqual(x - (centre_x - largeur / 2), 0)
            self.assertLessEqual(x - (centre_x - largeur / 2), largeur)
            self.assertGreaterEqual(y - (centre_y - hauteur / 2), 0)
            self.assertLessEqual(y - (centre_y - hauteur / 2), hauteur)

    def test_png_osm_contient_les_noms_et_les_marqueurs(self):
        tuile = Image.new("RGB", (256, 256), "#DDEEDD")
        with (
            patch("ui.maps.static_osm._charger_tuile", return_value=tuile),
            patch.object(ImageDraw.ImageDraw, "text", autospec=True) as texte,
        ):
            png = generer_carte_osm_png(self.points)

        image = Image.open(io.BytesIO(png))
        self.assertEqual(image.size, (900, 380))
        textes = [appel.args[2] for appel in texte.call_args_list]
        for nom in ("P1", "P2", "P3"):
            self.assertIn(nom, textes)
        pixels_rouges = sum(
            1 for pixel in image.getdata()
            if pixel[0] > 180 and pixel[1] < 110 and pixel[2] < 110
        )
        self.assertGreater(pixels_rouges, 50)

    def test_coordonnees_invalides_ne_creent_pas_de_marqueur(self):
        points = [
            PointCarte("Invalide", "x", 2.0),
            PointCarte("Valide", 45.0, 2.0),
        ]
        tuile = Image.new("RGB", (256, 256), "white")
        with (
            patch("ui.maps.static_osm._charger_tuile", return_value=tuile),
            patch.object(ImageDraw.ImageDraw, "text", autospec=True) as texte,
        ):
            generer_carte_osm_png(points)
        textes = [appel.args[2] for appel in texte.call_args_list]
        self.assertIn("Valide", textes)
        self.assertNotIn("Invalide", textes)

    def test_indisponibilite_osm_declenche_une_erreur_explicite(self):
        with patch(
            "ui.maps.static_osm._charger_tuile", side_effect=OSError("hors ligne")
        ):
            with self.assertRaisesRegex(OSError, "Aucune tuile"):
                generer_carte_osm_png(self.points)

    def test_pdf_utilise_la_carte_matplotlib_si_osm_est_indisponible(self):
        mixin = PdfChartsMixin()
        png_secours = b"png-secours"
        with (
            patch(
                "services.pdf.charts.generer_carte_osm_png",
                side_effect=OSError("hors ligne"),
            ),
            patch(
                "services.pdf.charts.charts.rendre_figure_png",
                return_value=png_secours,
            ) as rendre,
        ):
            resultat = mixin._generer_carte_pdf_png(self.points)

        self.assertEqual(resultat, png_secours)
        rendre.assert_called_once()


if __name__ == "__main__":
    unittest.main()
