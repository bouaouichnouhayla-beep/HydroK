"""Tests d'intégrité relationnelle exécutés sur une base temporaire."""

import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path

from database.connection import get_connection
from database.init_db import creer_base
from models import Entonnoir, PointMesure, Repetition, Sonde, Zone
from repositories.outil_repository import OutilRepository
from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository
from repositories.sonde_repository import SondeRepository
from repositories.zone_repository import ZoneRepository
from services.export_csv_service import ExportCsvService
from services.export_pdf_service import ExportPdfService
from services.synthese_table_service import SyntheseTableService


class DatabaseIntegrityTest(unittest.TestCase):

    def setUp(self):
        self.temporaire = tempfile.TemporaryDirectory()
        self.dossier = Path(self.temporaire.name)
        self.db_path = self.dossier / "conductivite.db"
        creer_base(self.db_path)
        self.zone_repo = ZoneRepository(self.db_path)
        self.point_repo = PointRepository(self.db_path)
        self.repetition_repo = RepetitionRepository(self.db_path)
        self.sonde_repo = SondeRepository(self.db_path)
        self.outil_repo = OutilRepository(self.db_path)

    def tearDown(self):
        self.temporaire.cleanup()

    def _ajouter_zone(self, nom):
        return self.zone_repo.ajouter(Zone(
            nom=nom, site="Site", date_campagne="2026-07-28",
            operateur="Test",
        ))

    def _ajouter_point(self, zone_id, nom):
        return self.point_repo.ajouter(PointMesure(
            zone_id=zone_id, nom=nom, facies="radier",
            latitude=45.1, longitude=4.8,
        ))

    def _ajouter_repetition(self, point_id, sonde_id=None, outil_id=None):
        return self.repetition_repo.ajouter(Repetition(
            point_id=point_id, sonde_id=sonde_id, outil_id=outil_id,
            methode="entonnoir", profondeur_enfoncement=0.35,
            hauteur_eau=0.2, hauteur_air=0.1, temps_infiltration=12.5,
            volume_eau=1.0, k_calcule=2.9e-4,
        ))

    def _service_synthese(self):
        service = SyntheseTableService()
        service.zone_repo = self.zone_repo
        service.point_repo = self.point_repo
        service.repetition_repo = self.repetition_repo
        service.sonde_repo = self.sonde_repo
        service.outil_repo = self.outil_repo
        return service

    def test_suppression_zone_cascade_points_et_repetitions(self):
        zone_id = self._ajouter_zone("Cascade étude")
        point_id = self._ajouter_point(zone_id, "P1")
        repetition_id = self._ajouter_repetition(point_id)

        self.zone_repo.supprimer(zone_id)

        self.assertIsNone(self.point_repo.trouver_par_id(point_id))
        self.assertIsNone(
            self.repetition_repo.trouver_par_id(repetition_id)
        )

    def test_suppression_point_cascade_plusieurs_repetitions(self):
        zone_id = self._ajouter_zone("Cascade point")
        point_id = self._ajouter_point(zone_id, "P2")
        repetition_ids = [
            self._ajouter_repetition(point_id) for _ in range(3)
        ]

        self.point_repo.supprimer(point_id)

        for repetition_id in repetition_ids:
            self.assertIsNone(
                self.repetition_repo.trouver_par_id(repetition_id)
            )

    def test_suppression_materiel_met_les_references_a_null(self):
        zone_id = self._ajouter_zone("Historique matériel")
        point_id = self._ajouter_point(zone_id, "P3")
        sonde_id = self.sonde_repo.ajouter(Sonde(
            nom="Sonde test", longueur_totale=2.4,
            diametre_interieur=0.02, longueur_crepine=0.25,
        ))
        outil_id = self.outil_repo.ajouter_entonnoir(Entonnoir(
            nom="Entonnoir test", type_outil="entonnoir",
            L1=0.1, L2=0.09, D1=0.02, D2=0.03, D3=0.2,
        ))
        repetition_id = self._ajouter_repetition(
            point_id, sonde_id, outil_id
        )

        self.sonde_repo.supprimer(sonde_id)
        repetition = self.repetition_repo.trouver_par_id(repetition_id)
        self.assertIsNotNone(repetition)
        self.assertIsNone(repetition.sonde_id)
        self.assertEqual(repetition.outil_id, outil_id)

        self.outil_repo.supprimer(outil_id)
        repetition = self.repetition_repo.trouver_par_id(repetition_id)
        self.assertIsNotNone(repetition)
        self.assertIsNone(repetition.sonde_id)
        self.assertIsNone(repetition.outil_id)

        service = self._service_synthese()
        donnees = service.pour_zone(zone_id)
        self.assertEqual(len(donnees.repetitions), 1)
        self.assertIsNone(donnees.repetitions[0].nom_sonde)
        self.assertIsNone(donnees.repetitions[0].nom_outil)

        csv_service = ExportCsvService(service)
        csv_paths = csv_service.exporter_zone(
            zone_id, "Historique matériel", self.dossier,
            instant=datetime(2026, 7, 28, 12, 0),
        )
        self.assertTrue(all(path.is_file() for path in csv_paths))

        pdf_service = ExportPdfService(
            service, self.zone_repo, self.point_repo, self.repetition_repo,
        )
        pdf_path = pdf_service.exporter_zone(
            zone_id, "Historique matériel", self.dossier,
            instant=datetime(2026, 7, 28, 12, 0),
        )
        self.assertTrue(pdf_path.is_file())

    def test_foreign_key_check_sans_violation(self):
        with closing(get_connection(self.db_path)) as connexion:
            self.assertEqual(
                connexion.execute("PRAGMA foreign_key_check").fetchall(), []
            )


if __name__ == "__main__":
    unittest.main()
