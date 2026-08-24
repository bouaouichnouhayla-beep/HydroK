"""Document, sommaire et pagination du rapport HydroK."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus.tableofcontents import TableOfContents


class RapportHydroK(SimpleDocTemplate):
    """Document ReportLab qui alimente automatiquement le sommaire."""

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        niveaux = {
            "TitreSection": 0,
            "TitreSousSection": 0,
            "TitreConclusion": 0,
        }
        niveau = niveaux.get(flowable.style.name)
        if niveau is None:
            return
        texte = flowable.getPlainText()
        cle = f"section-{self.seq.nextf('section')}"
        self.canv.bookmarkPage(cle)
        self.canv.addOutlineEntry(texte, cle, level=niveau, closed=False)
        self.notify("TOCEntry", (niveau, texte, self.page, cle))


def creer_sommaire():
    sommaire = TableOfContents()
    sommaire.levelStyles = [
        ParagraphStyle(
            "SommaireNiveau1", fontName="Helvetica-Bold",
            fontSize=10, leading=16, leftIndent=0,
            firstLineIndent=0, textColor=colors.HexColor("#173A46"),
        ),
        ParagraphStyle(
            "SommaireNiveau2", fontName="Helvetica",
            fontSize=9, leading=14, leftIndent=12,
            firstLineIndent=0, textColor=colors.HexColor("#46565D"),
        ),
    ]
    return sommaire


def ajouter_numero_page(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#59666C"))
    canvas.drawRightString(
        landscape(A4)[0] - 15 * mm,
        8 * mm,
        f"Page {document.page}",
    )
    canvas.restoreState()


def construire_document(chemin, histoire):
    document = RapportHydroK(
        str(chemin), pagesize=landscape(A4),
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="HydroK — Rapport de mesure de conductivité hydraulique",
        author="HydroK",
    )
    document.multiBuild(
        histoire,
        onFirstPage=ajouter_numero_page,
        onLaterPages=ajouter_numero_page,
    )
