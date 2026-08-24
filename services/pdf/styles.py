"""Styles ReportLab du rapport HydroK."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm


def creer_styles():
    styles = getSampleStyleSheet()
    return {
        "couverture_marque": ParagraphStyle(
            "CouvertureMarque", parent=styles["Title"],
            fontName="Helvetica-Bold", fontSize=30, leading=34,
            alignment=TA_CENTER, textColor=colors.HexColor("#173A46"),
        ),
        "couverture_titre": ParagraphStyle(
            "CouvertureTitre", parent=styles["Heading1"],
            fontName="Helvetica", fontSize=19, leading=24,
            alignment=TA_CENTER, textColor=colors.HexColor("#263238"),
        ),
        "couverture_etude": ParagraphStyle(
            "CouvertureEtude", parent=styles["Heading2"],
            fontName="Helvetica-Bold", fontSize=16, leading=20,
            alignment=TA_CENTER, textColor=colors.HexColor("#263238"),
        ),
        "mention_couverture": ParagraphStyle(
            "MentionCouverture", parent=styles["BodyText"],
            fontName="Helvetica", fontSize=9, leading=12,
            alignment=TA_CENTER, textColor=colors.HexColor("#59666C"),
        ),
        "titre_sommaire": ParagraphStyle(
            "TitreSommaire", parent=styles["Heading1"],
            fontName="Helvetica-Bold", fontSize=20, leading=24,
            textColor=colors.HexColor("#173A46"),
        ),
        "titre_section": ParagraphStyle(
            "TitreSection", parent=styles["Heading2"],
            fontName="Helvetica-Bold", fontSize=14, leading=17,
            spaceAfter=2, textColor=colors.HexColor("#173A46"),
        ),
        "titre_sous_section": ParagraphStyle(
            "TitreSousSection", parent=styles["Heading3"],
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=colors.HexColor("#334E58"),
        ),
        "legende_figure": ParagraphStyle(
            "LegendeFigure", parent=styles["BodyText"],
            fontName="Helvetica-Oblique", fontSize=9, leading=12,
            alignment=TA_CENTER, textColor=colors.HexColor("#46565D"),
        ),
        "texte_rapport": ParagraphStyle(
            "TexteRapport", parent=styles["BodyText"],
            fontName="Helvetica", fontSize=9, leading=13,
            textColor=colors.HexColor("#263238"),
        ),
        "titre_conclusion": ParagraphStyle(
            "TitreConclusion", parent=styles["Heading1"],
            fontName="Helvetica-Bold", fontSize=22, leading=26,
            alignment=TA_CENTER, textColor=colors.HexColor("#173A46"),
        ),
        "conclusion_texte": ParagraphStyle(
            "ConclusionTexte", parent=styles["BodyText"],
            fontName="Helvetica", fontSize=13, leading=18,
            alignment=TA_CENTER, textColor=colors.HexColor("#263238"),
        ),
        "conclusion_description": ParagraphStyle(
            "ConclusionDescription", parent=styles["BodyText"],
            fontName="Helvetica", fontSize=11, leading=17,
            alignment=TA_CENTER, leftIndent=25 * mm, rightIndent=25 * mm,
            textColor=colors.HexColor("#263238"),
        ),
        "entete_tableau": ParagraphStyle(
            "EnteteTableau", parent=styles["BodyText"],
            fontName="Helvetica-Bold", fontSize=7, leading=8,
            textColor=colors.HexColor("#263238"),
        ),
        "cellule": ParagraphStyle(
            "Cellule", parent=styles["BodyText"],
            fontName="Helvetica", fontSize=7, leading=9,
        ),
        "cellule_petite": ParagraphStyle(
            "CellulePetite", parent=styles["BodyText"],
            fontName="Helvetica", fontSize=5.5, leading=6.5,
        ),
        "cellule_gras": ParagraphStyle(
            "CelluleGras", parent=styles["BodyText"],
            fontName="Helvetica-Bold", fontSize=8, leading=10,
        ),
    }
