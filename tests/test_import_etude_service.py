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
from services.import_etude_service import ImportEtudeError, import_etude


class ImportEtudeServiceTest(unittest.TestCase):
    def setUp(self):
        self.temporaire = tempfile.TemporaryDirectory()
        self.dossier = Path(self.temporaire.name)
        self.base_a = self.dossier / "a.db"
        self.base_b = self.dossier / "b.db"
        creer_base(self.base_a)
        creer_base(self.base_b)
        self.repos_a = self._repos(self.base_a)
        self.repos_b = self._repos(self.base_b)

    @staticmethod
    def _repos(db):
        return (ZoneRepository(db), PointRepository(db), RepetitionRepository(db),
                SondeRepository(db), OutilRepository(db))

    def tearDown(self):
        self.temporaire.cleanup()

    def _export_source(self):
        zones, points, repetitions, sondes, outils = self.repos_a
        zone_id = zones.ajouter(Zone("Étude Rhône", "Site", "2026-08-28", "Op"))
        point_id = points.ajouter(PointMesure(zone_id, "P1", "radier", 45.1, 4.8, "GPS"))
        sonde_id = sondes.ajouter(Sonde("S1", 2.0, 0.02, 0.25))
        outil_id = outils.ajouter_entonnoir(Entonnoir(
            "E1", "entonnoir", 0.1, 0.09, 0.02, 0.03, 0.2,
        ))
        repetitions.ajouter(Repetition(
            point_id, sonde_id, outil_id, "entonnoir", 0.35, 0.2, 0.1,
            12.5, 1.0, None, None, 2.9e-4, "mesure",
        ))
        fichier = export_etude(zone_id, self.dossier / "etude.hydrok", db_path=self.base_a)
        return fichier, zone_id, point_id, sonde_id, outil_id

    def test_import_recree_etude_relations_et_valeurs(self):
        fichier, old_zone, old_point, old_sonde, old_outil = self._export_source()
        zones_b, points_b, repetitions_b, sondes_b, outils_b = self.repos_b
        # Décale les séquences pour vérifier que les IDs source ne sont pas imposés.
        zone_existante = zones_b.ajouter(Zone("Préexistante", "S", "2026", "O"))
        points_b.ajouter(PointMesure(zone_existante, "P0", "berge"))
        sondes_b.ajouter(Sonde("S0", 1.0, 0.01, 0.1))
        outils_b.ajouter_entonnoir(Entonnoir(
            "E0", "entonnoir", 0.1, 0.09, 0.02, 0.03, 0.2,
        ))
        new_zone = import_etude(fichier, self.base_b)
        self.assertNotEqual(new_zone, old_zone)
        zone = zones_b.trouver_par_id(new_zone)
        self.assertEqual(zone.nom, "Étude Rhône")
        point = points_b.lister_par_zone(new_zone)[0]
        self.assertNotEqual(point.id, old_point)
        repetition = repetitions_b.lister_par_point(point.id)[0]
        self.assertEqual(repetition.point_id, point.id)
        self.assertEqual(repetition.profondeur_enfoncement, 0.35)
        self.assertEqual(repetition.k_calcule, 2.9e-4)
        self.assertNotEqual(repetition.sonde_id, old_sonde)
        self.assertNotEqual(repetition.outil_id, old_outil)
        self.assertEqual(sondes_b.trouver_par_id(repetition.sonde_id).nom, "S1")
        self.assertEqual(outils_b.trouver_par_id(repetition.outil_id).nom, "E1")

    def test_collision_de_nom_ne_remplace_pas_etude_existante(self):
        fichier, *_ = self._export_source()
        zones_b = self.repos_b[0]
        existante = zones_b.ajouter(Zone("Étude Rhône", "Autre", "2026", "O"))
        nouvelle = import_etude(fichier, self.base_b)
        self.assertNotEqual(nouvelle, existante)
        self.assertEqual(zones_b.trouver_par_id(existante).site, "Autre")
        self.assertEqual(zones_b.trouver_par_id(nouvelle).nom, "Étude Rhône (importée)")

    def test_fichier_invalide_refuse(self):
        invalide = self.dossier / "invalide.hydrok"
        invalide.write_bytes(b"pas un zip")
        with self.assertRaises(ImportEtudeError):
            import_etude(invalide, self.base_b)

    def test_erreur_pendant_import_rollback_tout(self):
        fichier, *_ = self._export_source()
        corrompu = self.dossier / "corrompu.hydrok"
        with ZipFile(fichier) as source, ZipFile(corrompu, "w") as cible:
            cible.writestr("manifest.json", source.read("manifest.json"))
            study = json.loads(source.read("study.json"))
            study["repetitions"][0]["point_id"] = 999999
            cible.writestr("study.json", json.dumps(study))
        zones_b = self.repos_b[0]
        avant = len(zones_b.lister())
        with self.assertRaises(ImportEtudeError):
            import_etude(corrompu, self.base_b)
        self.assertEqual(len(zones_b.lister()), avant)


if __name__ == "__main__":
    unittest.main()
