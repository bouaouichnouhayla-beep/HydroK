"""Construction des tableaux ReportLab du rapport HydroK."""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle


COLONNES_REPETITIONS = (
    "Point", "Numéro de répétition", "Méthode",
    "Profondeur h_p (cm)", "Hauteur d'eau h_w (m)",
    "Hauteur d'air h_a (m)", "Volume d'eau (L)", "Hauteur début (m)",
    "Hauteur fin (m)", "Temps d'infiltration (s)", "Référence outil",
    "Référence sonde", "Conductivité hydraulique K (m/s)", "Commentaire",
)


class PdfTablesMixin:

    def _table_info(self, lignes, largeurs=None):
        donnees = [
            [self._paragraphe(cle, "cellule_gras"), self._paragraphe(valeur)]
            for cle, valeur in lignes
        ]
        table = Table(donnees, colWidths=largeurs or (62 * mm, 190 * mm))
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F2F3")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8BEC3")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        table.hAlign = "CENTER" if largeurs else "LEFT"
        return table

    def _table_points(self, points, moyennes_k):
        lignes = [["Point", "Latitude", "Longitude", "Faciès", "K moyen (m/s)"]]
        lignes.extend([
            [
                point.nom,
                self._format_decimal(point.latitude, 6),
                self._format_decimal(point.longitude, 6),
                point.facies,
                self._format_k_pdf(moyennes_k.get(point.id), avec_unite=True),
            ]
            for point in points
        ])
        return self._tableau(lignes, (55 * mm, 42 * mm, 42 * mm, 55 * mm, 55 * mm))

    def _table_repetitions(self, repetitions):
        lignes = [list(self.COLONNES_REPETITIONS)]
        lignes.extend([
            [
                ligne.nom_point,
                ligne.numero_repetition,
                ligne.methode,
                self._format_profondeur_cm(ligne.profondeur_enfoncement),
                self._format_decimal(ligne.hauteur_eau, 3, fixe=True),
                self._format_decimal(ligne.hauteur_air, 3, fixe=True),
                self._format_decimal(ligne.volume_eau, 3),
                self._format_decimal(ligne.h_debut, 3, fixe=True),
                self._format_decimal(ligne.h_fin, 3, fixe=True),
                self._format_decimal(ligne.temps_infiltration, 2),
                ligne.nom_outil,
                ligne.nom_sonde,
                self._format_k_pdf(ligne.k_calcule, "cellule_petite"),
                ligne.commentaire,
            ]
            for ligne in repetitions
        ])
        largeurs = tuple(
            largeur * mm for largeur in
            (16, 15, 15, 19, 17, 17, 15, 17, 17, 19, 19, 19, 24, 30)
        )
        return self._tableau(lignes, largeurs, petite=True)

    def _table_materiel(self, materiels):
        lignes = [["Référence", "Catégorie", "Type", "Paramètres"]]
        lignes.extend([
            [
                ligne.nom,
                ligne.categorie.capitalize(),
                "Sonde" if ligne.categorie == "sonde"
                else (ligne.type_materiel or "").capitalize(),
                self._parametres_materiel(ligne),
            ]
            for ligne in materiels
        ])
        return self._tableau(lignes, (60 * mm, 42 * mm, 45 * mm, 112 * mm))

    def _tableau(self, lignes, largeurs, petite=False):
        style_cellule = "cellule_petite" if petite else "cellule"
        donnees = [
            [self._paragraphe(valeur, "entete_tableau" if index == 0 else style_cellule)
             for valeur in ligne]
            for index, ligne in enumerate(lignes)
        ]
        table = Table(donnees, colWidths=largeurs, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE4E7")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#AEB7BC")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table
