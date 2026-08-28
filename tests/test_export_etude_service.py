import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from database.init_db import creer_base
from models import Entonnoir, PointMesure, Repetition, Sonde, Zone
from repositories.outil_repository import OutilRepository
from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository
from repositories.sonde_repository import SondeRepository
from repositories.zone_repository import ZoneRepository
from services.export_etude_service import export_etude


class ExportEtudeServiceTest(unittest.TestCase):
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

    def test_exporte_une_seule_etude_avec_points_repetitions(self):
        zone_id = self.zone_repo.ajouter(Zone(
            nom="Étude exportée", site="Site A", date_campagne="2026-08-28",
            operateur="Test",
        ))
        autre_zone_id = self.zone_repo.ajouter(Zone(
            nom="À ne pas exporter", site="Site B", date_campagne="2026-08-29",
            operateur="Test",
        ))
        point_id = self.point_repo.ajouter(PointMesure(
            zone_id=zone_id, nom="P1", facies="radier", latitude=45.1,
            longitude=4.8, commentaires="GPS",
        ))
        autre_point_id = self.point_repo.ajouter(PointMesure(
            zone_id=autre_zone_id, nom="P2", facies="berge",
        ))
        sonde_id = self.sonde_repo.ajouter(Sonde(
            nom="S1", longueur_totale=2.0, diametre_interieur=0.02,
            longueur_crepine=0.25,
        ))
        outil_id = self.outil_repo.ajouter_entonnoir(Entonnoir(
            nom="E1", type_outil="entonnoir", L1=0.1, L2=0.09,
            D1=0.02, D2=0.03, D3=0.2,
        ))
        self.repetition_repo.ajouter(Repetition(
            point_id=point_id, sonde_id=sonde_id, outil_id=outil_id,
            methode="entonnoir", profondeur_enfoncement=0.35,
            hauteur_eau=0.2, hauteur_air=0.1, temps_infiltration=12.5,
            volume_eau=1.0, k_calcule=2.9e-4,
        ))
        self.repetition_repo.ajouter(Repetition(
            point_id=autre_point_id, sonde_id=None, outil_id=None,
            methode="entonnoir", profondeur_enfoncement=0.1,
            hauteur_eau=0.2, hauteur_air=0.1, temps_infiltration=5.0,
        ))

        destination = export_etude(zone_id, self.dossier / "etude.hydrok", db_path=self.db_path)
        self.assertTrue(destination.is_file())
        with ZipFile(destination) as archive:
            self.assertEqual(set(archive.namelist()), {"manifest.json", "study.json"})
            manifest = json.loads(archive.read("manifest.json"))
            study = json.loads(archive.read("study.json"))
        self.assertEqual(manifest["format"], "HydroK")
        self.assertEqual(manifest["format_version"], 1)
        self.assertEqual(study["zone"]["id"], zone_id)
        self.assertEqual([point["nom"] for point in study["points"]], ["P1"])
        self.assertEqual(len(study["repetitions"]), 1)
        self.assertEqual(study["repetitions"][0]["point_id"], point_id)
        self.assertEqual([sonde["id"] for sonde in study["sondes"]], [sonde_id])
        self.assertEqual([outil["id"] for outil in study["outils"]], [outil_id])


if __name__ == "__main__":
    unittest.main()
