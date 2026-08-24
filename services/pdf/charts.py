"""Intégration des graphiques existants dans le rapport PDF."""

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, PageBreak, Paragraph, Spacer, Table, TableStyle,
)

from ui import charts
from ui.maps import PointCarte
from ui.maps.interactive_map import normaliser_points
from ui.maps.static_osm import generer_carte_osm_png
from utils.logging_config import obtenir_logger


logger = obtenir_logger(__name__)


class PdfChartsMixin:

    def _section_graphiques(self, nom_etude, points, moyennes_k, donnees):
        """Insère les figures existantes, sans redéfinir leur dessin."""
        repetitions_par_point = {point.nom: [] for point in points}
        for ligne in donnees.repetitions:
            repetitions_par_point.setdefault(ligne.nom_point, []).append(ligne)

        noms_points = [point.nom for point in points]
        valeurs_par_point = [
            [ligne.k_calcule for ligne in repetitions_par_point.get(point.nom, [])
             if ligne.k_calcule is not None]
            for point in points
        ]
        k_zone = [
            ligne.k_calcule for ligne in donnees.repetitions
            if ligne.k_calcule is not None
        ]
        facies = {}
        methodes = {}
        profondeurs = {}
        for point in points:
            libelle = point.facies or "—"
            facies[libelle] = facies.get(libelle, 0) + 1
        for ligne in donnees.repetitions:
            methode = ligne.methode or "—"
            methodes[methode] = methodes.get(methode, 0) + 1
            if ligne.profondeur_enfoncement is not None:
                profondeur = round(ligne.profondeur_enfoncement * 100, 2)
                profondeurs[profondeur] = profondeurs.get(profondeur, 0) + 1

        graphiques = [
            ("Répartition des points par faciès", lambda: (
                charts.graphique_repartition_facies(
                    list(facies), list(facies.values()), figsize=(7.2, 3.8)
                )
            )),
            ("Distribution des valeurs de K", lambda: (
                charts.graphique_histogramme(
                    k_zone, figsize=(9.0, 3.8),
                    titre="Distribution des valeurs de K",
                )
            )),
            ("Dispersion de K par point", lambda: (
                charts.graphique_boxplot_k_par_point(
                    noms_points, valeurs_par_point, figsize=(9.0, 3.8)
                )
            )),
            ("Répartition des méthodes utilisées", lambda: (
                charts.graphique_repartition_methodes(
                    list(methodes), list(methodes.values()), figsize=(7.2, 3.8)
                )
            )),
            ("Répartition des profondeurs mesurées", lambda: (
                charts.graphique_repartition_profondeurs(
                    sorted(profondeurs),
                    [profondeurs[p] for p in sorted(profondeurs)],
                    figsize=(7.2, 3.8),
                )
            )),
        ]
        points_carte = [
            PointCarte(
                nom=point.nom,
                latitude=point.latitude,
                longitude=point.longitude,
                facies=point.facies,
                k_moyen=moyennes_k.get(point.id),
            )
            for point in points
        ]
        index_carte = None
        if normaliser_points(points_carte):
            index_carte = len(graphiques)
            graphiques.append((
                "Localisation des points de mesure",
                lambda: self._generer_carte_pdf_png(points_carte),
            ))

        histoire = []
        for index in range(0, len(graphiques), 2):
            if index_carte is not None and index == index_carte - 1:
                titre_graphique, fabrique_graphique = graphiques[index]
                titre_carte, fabrique_carte = graphiques[index_carte]
                cellule_graphique = self._cellule_graphique(
                    titre_graphique, fabrique_graphique, index + 1,
                )
                cellule_carte = self._cellule_png(
                    titre_carte, fabrique_carte(), index_carte + 1,
                    largeur_max=238 * mm, hauteur_max=62 * mm,
                )
                grille = Table(
                    [[cellule_graphique, []], [cellule_carte, None]],
                    colWidths=(123 * mm, 123 * mm),
                    hAlign="CENTER",
                )
                grille.setStyle(TableStyle([
                    ("SPAN", (0, 1), (1, 1)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("BOX", (0, 0), (-1, -1), 0, colors.white),
                ]))
                histoire.extend((PageBreak(), grille))
                break

            cellules = []
            for decalage, (titre, fabrique) in enumerate(
                graphiques[index:index + 2]
            ):
                numero = index + decalage + 1
                if index + decalage == index_carte:
                    cellules.append(self._cellule_png(
                        titre, fabrique(), numero, largeur_max=115 * mm,
                    ))
                else:
                    cellules.append(self._cellule_graphique(
                        titre, fabrique, numero,
                    ))
            if len(cellules) == 1:
                cellules.append([])

            grille = Table(
                [cellules], colWidths=(123 * mm, 123 * mm),
                hAlign="CENTER",
            )
            grille.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOX", (0, 0), (-1, -1), 0, colors.white),
            ]))
            histoire.extend((PageBreak(), grille))
        return histoire

    def _generer_carte_pdf_png(self, points_carte):
        """Génère la carte OSM, ou l'ancienne carte en cas d'indisponibilité."""
        try:
            return generer_carte_osm_png(
                points_carte, largeur=1400, hauteur=340,
            )
        except Exception:  # Le fond distant ne doit jamais bloquer le rapport.
            logger.exception(
                "Carte OpenStreetMap indisponible ; utilisation du rendu de secours"
            )
            points_valides = normaliser_points(points_carte)
            figure = lambda: charts.graphique_carte_points(
                [longitude for _, _, longitude in points_valides],
                [latitude for _, latitude, _ in points_valides],
                [point.nom for point, _, _ in points_valides],
                [point.k_moyen for point, _, _ in points_valides],
                figsize=(9.0, 3.8),
            )
            return charts.rendre_figure_png(
                lambda: self._figure_sans_titre(figure)
            )

    def _cellule_graphique(self, titre, fabrique, numero):
        png = charts.rendre_figure_png(
            lambda: self._figure_sans_titre(fabrique)
        )
        return self._cellule_png(titre, png, numero)

    def _cellule_png(
        self, titre, png, numero, largeur_max=112 * mm,
        hauteur_max=105 * mm,
    ):
        flux = io.BytesIO(png)
        image = Image(flux)
        facteur = min(
            largeur_max / image.imageWidth,
            hauteur_max / image.imageHeight,
        )
        image.drawWidth = image.imageWidth * facteur
        image.drawHeight = image.imageHeight * facteur
        image.hAlign = "CENTER"
        image._hydrok_buffer = flux
        return [
            Paragraph(titre, self.styles["titre_sous_section"]),
            Spacer(1, 3 * mm),
            image,
            Spacer(1, 2 * mm),
            Paragraph(
                f"Figure {numero} — {escape(titre)}.",
                self.styles["legende_figure"],
            ),
        ]

    @staticmethod
    def _figure_sans_titre(fabrique):
        """Allège le titre interne sans modifier le graphique source."""
        figure = fabrique()
        if figure._suptitle is not None:
            figure._suptitle.set_text("")
        for axe in figure.axes:
            axe.set_title("")
        return figure
