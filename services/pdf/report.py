"""Composition ordonnée des sections du rapport PDF HydroK."""

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Image, PageBreak, Paragraph, Spacer

from ui.maps import PointCarte
from version import APPLICATION_VERSION


class PdfReportMixin:

    def _construire_rapport(
        self, zone, nom_etude, points, moyennes_k, donnees, instant,
    ):
        """Assemble les composants ReportLab dans leur ordre de lecture."""
        methodes = sorted({
            ligne.methode for ligne in donnees.repetitions if ligne.methode
        })
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
        flux_carte = io.BytesIO(self._generer_carte_pdf_png(
            points_carte, largeur=1400, hauteur=650,
            figsize_secours=(14.0, 6.5),
        ))
        carte_couverture = Image(flux_carte)
        facteur_carte = min(
            245 * mm / carte_couverture.imageWidth,
            85 * mm / carte_couverture.imageHeight,
        )
        carte_couverture.drawWidth *= facteur_carte
        carte_couverture.drawHeight *= facteur_carte
        carte_couverture.hAlign = "CENTER"
        carte_couverture._hydrok_buffer = flux_carte

        histoire = [
            Spacer(1, 12 * mm),
            Paragraph("HydroK", self.styles["couverture_marque"]),
            Spacer(1, 5 * mm),
            HRFlowable(
                width="48%", thickness=1.2,
                color=colors.HexColor("#55747E"), spaceBefore=4, spaceAfter=12,
            ),
            Paragraph(
                "Rapport de mesure de conductivité hydraulique",
                self.styles["couverture_titre"],
            ),
            Spacer(1, 7 * mm),
            Paragraph(escape(str(nom_etude)), self.styles["couverture_etude"]),
            Spacer(1, 5 * mm),
        ]
        histoire.extend((
            Paragraph(
                "Date de génération : "
                f"{instant.strftime('%d/%m/%Y %H:%M')}",
                self.styles["mention_couverture"],
            ),
            Spacer(1, 5 * mm),
            carte_couverture,
            PageBreak(),
            Paragraph("Sommaire", self.styles["titre_sommaire"]),
            Spacer(1, 8 * mm),
            self._creer_sommaire(),
            PageBreak(),
            Paragraph("Résumé de la campagne", self.styles["titre_section"]),
            Spacer(1, 4 * mm),
            Paragraph(
                "Cette section synthétise le périmètre de la campagne "
                "de mesure enregistrée dans HydroK.",
                self.styles["texte_rapport"],
            ),
            Spacer(1, 5 * mm),
            self._table_info((
                ("Nombre de points", len(points)),
                ("Nombre de répétitions", len(donnees.repetitions)),
                ("Nombre de matériels", len(donnees.materiels)),
                ("Méthodes utilisées", ", ".join(
                    self._format_valeur_technique(methode)
                    for methode in methodes
                ) or "Aucune"),
            )),
            Spacer(1, 9 * mm),
        ))

        histoire.extend((
            Paragraph("Informations générales", self.styles["titre_section"]),
            Spacer(1, 4 * mm),
            self._table_info(self._informations_zone(zone, nom_etude)),
            Spacer(1, 9 * mm),
            Paragraph("Tableau des points", self.styles["titre_section"]),
            Spacer(1, 4 * mm),
            self._table_points(points, moyennes_k),
            PageBreak(),
            Paragraph("Tableau des répétitions", self.styles["titre_section"]),
            Spacer(1, 4 * mm),
            self._table_repetitions(donnees.repetitions),
            PageBreak(),
            Paragraph("Tableau du matériel", self.styles["titre_section"]),
            Spacer(1, 4 * mm),
            self._table_materiel(donnees.materiels),
        ))
        histoire.extend(self._section_graphiques(
            nom_etude, points, moyennes_k, donnees
        ))
        histoire.extend((
            PageBreak(),
            Spacer(1, 18 * mm),
            Paragraph("Conclusion", self.styles["titre_conclusion"]),
            Spacer(1, 9 * mm),
            Paragraph(
                self._texte_conclusion(points, moyennes_k, donnees),
                self.styles["conclusion_description"],
            ),
            Spacer(1, 12 * mm),
            Paragraph(
                "Rapport généré automatiquement par HydroK",
                self.styles["conclusion_texte"],
            ),
            Spacer(1, 6 * mm),
            self._table_info((
                ("Date de génération", instant.strftime("%d/%m/%Y %H:%M")),
                ("Version de l'application", APPLICATION_VERSION),
            ), largeurs=(65 * mm, 70 * mm)),
        ))
        return histoire

    def _informations_zone(self, zone, nom_etude):
        return (
            ("Nom de l'étude", nom_etude),
            ("Site", zone.site if zone else None),
            ("Localisation", zone.localisation if zone else None),
            ("Date de campagne", zone.date_campagne if zone else None),
            ("Opérateur", zone.operateur if zone else None),
            ("État", self._format_valeur_technique(zone.etat) if zone else None),
            ("Remarques", zone.remarques if zone else None),
        )

    def _texte_conclusion(self, points, moyennes_k, donnees):
        nombre_points = len(points)
        nombre_repetitions = len(donnees.repetitions)
        texte = (
            f"L'étude comprend {nombre_points} point"
            f"{'s' if nombre_points != 1 else ''} de mesure et "
            f"{nombre_repetitions} répétition"
            f"{'s' if nombre_repetitions != 1 else ''}."
        )
        methodes = sorted({
            str(ligne.methode).strip().lower()
            for ligne in donnees.repetitions if ligne.methode
        })
        if methodes:
            formulations = [f"par {methode}" for methode in methodes]
            terme = "de la méthode" if len(methodes) == 1 else "des méthodes"
            texte += (
                f" Les mesures ont été réalisées à l'aide {terme} "
                f"{self._enumeration(formulations)}."
            )

        valeurs = [
            (point, moyennes_k.get(point.id))
            for point in points if moyennes_k.get(point.id) is not None
        ]
        if valeurs:
            point_min, k_min = min(valeurs, key=lambda element: element[1])
            k_max = max(valeur for _, valeur in valeurs)
            texte += (
                " Les conductivités hydrauliques moyennes par point sont "
                f"comprises entre {self._format_k_markup(k_min)} et "
                f"{self._format_k_markup(k_max)} m/s. Le point "
                f"{escape(str(point_min.nom))} présente la conductivité "
                "hydraulique moyenne la plus faible."
            )
        return texte
