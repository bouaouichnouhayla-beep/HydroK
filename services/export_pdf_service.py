"""Point d'entrée compatible de l'export PDF HydroK."""

from datetime import datetime
from pathlib import Path

from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository
from repositories.zone_repository import ZoneRepository
from services.pdf.charts import PdfChartsMixin
from services.pdf.document import (
    ajouter_numero_page,
    construire_document,
    creer_sommaire,
)
from services.pdf.formatting import PdfFormattingMixin
from services.pdf.report import PdfReportMixin
from services.pdf.styles import creer_styles
from services.pdf.tables import (
    COLONNES_REPETITIONS as PDF_COLONNES_REPETITIONS,
    PdfTablesMixin,
)
from services.synthese_table_service import SyntheseTableService
from utils.logging_config import obtenir_logger


logger = obtenir_logger(__name__)


class ExportPdfService(
    PdfReportMixin,
    PdfChartsMixin,
    PdfTablesMixin,
    PdfFormattingMixin,
):
    """Compose un rapport A4 uniquement à partir des services existants."""

    COLONNES_REPETITIONS = PDF_COLONNES_REPETITIONS

    def __init__(
        self, synthese_table_service=None, zone_repo=None,
        point_repo=None, repetition_repo=None,
    ):
        self.synthese_table_service = (
            synthese_table_service or SyntheseTableService()
        )
        self.zone_repo = zone_repo or ZoneRepository()
        self.point_repo = point_repo or PointRepository()
        self.repetition_repo = repetition_repo or RepetitionRepository()
        self.styles = self._creer_styles()

    def exporter_zone(
        self, zone_id: int, nom_etude: str, dossier,
        *, ecraser: bool = False, instant=None,
    ) -> Path:
        """Crée le rapport PDF horodaté de l'étude et retourne son chemin."""
        instant = instant or datetime.now()
        horodatage = instant.strftime("%Y-%m-%d_%H-%M")
        nom_fichier = self._nom_fichier(nom_etude)
        chemin = Path(dossier) / f"{nom_fichier}_rapport_{horodatage}.pdf"
        if chemin.exists() and not ecraser:
            raise FileExistsError("Un rapport portant ce nom existe déjà.")

        zone = self.zone_repo.trouver_par_id(zone_id)
        points = self.point_repo.lister_par_zone(zone_id)
        donnees = self.synthese_table_service.pour_zone(zone_id)
        moyennes_k = {
            point.id: self.repetition_repo.moyenne_k_par_point(point.id)
            for point in points
        }
        histoire = self._construire_rapport(
            zone, nom_etude, points, moyennes_k, donnees, instant
        )
        self._construire_document(chemin, histoire)
        logger.info("Export PDF terminé : %s", chemin)
        return chemin

    @staticmethod
    def _construire_document(chemin, histoire):
        construire_document(chemin, histoire)

    @staticmethod
    def _creer_sommaire():
        return creer_sommaire()

    @staticmethod
    def _creer_styles():
        return creer_styles()

    _ajouter_numero_page = staticmethod(ajouter_numero_page)

    @staticmethod
    def _nom_fichier(nom_etude):
        nom = str(nom_etude).strip()
        for caractere in ('/', '\\'):
            nom = nom.replace(caractere, "_")
        return nom or "Etude"
