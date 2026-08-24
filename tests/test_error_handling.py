"""Tests ciblés de la gestion des erreurs HydroK."""

import ast
import io
import logging
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from database.init_db import creer_base
from repositories.zone_repository import ZoneRepository
from services.export_csv_service import ExportCsvService
from ui.error_handler import executer_callback_securise
from ui.schema_image import SchemaImage
from utils.validation import convertir_nombre


RACINE = Path(__file__).resolve().parent.parent


class ErrorHandlingTest(unittest.TestCase):

    def test_base_verrouillee_conserve_operational_error(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "verrouillee.db"
            creer_base(chemin)
            verrou = sqlite3.connect(chemin, timeout=0.01)
            verrou.execute("BEGIN EXCLUSIVE")
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    ZoneRepository(chemin).lister()
            finally:
                verrou.rollback()
                verrou.close()

    def test_export_permission_refusee_ne_produit_pas_de_succes(self):
        service = ExportCsvService(Mock())
        with patch("pathlib.Path.open", side_effect=PermissionError("secret")):
            with self.assertRaises(PermissionError):
                service._ecrire("sortie.csv", ("colonne",), [("valeur",)])

    def test_valeur_numerique_invalide(self):
        with self.assertRaisesRegex(ValueError, "doit être un nombre"):
            convertir_nombre("abc", "La profondeur", obligatoire=True)

    def test_image_inexistante_affiche_le_texte_alternatif(self):
        schema = SchemaImage.__new__(SchemaImage)
        schema._rendre = Mock()
        schema.afficher(RACINE / "image-inexistante.png", "Test")
        self.assertIsNone(schema._image_source)
        self.assertEqual(schema._message, "Schéma indisponible")
        schema._rendre.assert_called_once()

    def test_callback_inattendu_est_journalise_sans_detail_utilisateur(self):
        flux = io.StringIO()
        handler = logging.StreamHandler(flux)
        logger = logging.getLogger("hydrok.ui.error_handler")
        logger.addHandler(handler)
        try:
            with patch("ui.error_handler.messagebox.showerror") as afficher:
                executer_callback_securise(
                    lambda: (_ for _ in ()).throw(RuntimeError("detail-secret")),
                    contexte="test callback",
                )
            self.assertIn("Traceback", flux.getvalue())
            self.assertIn("detail-secret", flux.getvalue())
            self.assertNotIn("detail-secret", afficher.call_args.args[1])
        finally:
            logger.removeHandler(handler)

    def test_aucun_except_vide_ou_uniquement_pass(self):
        for chemin in RACINE.rglob("*.py"):
            if any(
                partie in {"__pycache__", ".venv", "venv"}
                for partie in chemin.parts
            ):
                continue
            arbre = ast.parse(chemin.read_text(encoding="utf-8"), filename=str(chemin))
            for noeud in ast.walk(arbre):
                if isinstance(noeud, ast.ExceptHandler):
                    self.assertFalse(
                        not noeud.body or all(isinstance(item, ast.Pass) for item in noeud.body),
                        f"Bloc except vide dans {chemin}:{noeud.lineno}",
                    )


if __name__ == "__main__":
    unittest.main()
