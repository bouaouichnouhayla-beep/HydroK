import unittest
from unittest.mock import Mock, patch

import ui.zone_frame as module_zones
from ui.zone_frame import ZoneFrame


class ZoneFrameExportImportTest(unittest.TestCase):
    def _frame(self, selection=None):
        frame = ZoneFrame.__new__(ZoneFrame)
        frame._selection = Mock(return_value=selection)
        frame.charger_zones = Mock()
        return frame

    def test_import_annule_ne_fait_aucune_operation(self):
        frame = self._frame()
        with (
            patch.object(module_zones.filedialog, "askopenfilename", return_value=""),
            patch.object(module_zones, "import_etude") as importer,
        ):
            frame._importer_etude()
        importer.assert_not_called()
        frame.charger_zones.assert_not_called()

    def test_import_appelle_service_et_rafraichit(self):
        frame = self._frame()
        with (
            patch.object(module_zones.filedialog, "askopenfilename", return_value="/tmp/a.hydrok"),
            patch.object(module_zones, "import_etude") as importer,
            patch.object(module_zones.messagebox, "showinfo") as info,
        ):
            frame._importer_etude()
        importer.assert_called_once_with("/tmp/a.hydrok")
        frame.charger_zones.assert_called_once_with()
        info.assert_called_once()

    def test_export_appelle_service_avec_id_selectionne(self):
        frame = self._frame((42, (1, "Étude : Rhône", "Site")))
        with (
            patch.object(module_zones.filedialog, "asksaveasfilename", return_value="/tmp/rhone.hydrok"),
            patch.object(module_zones, "export_etude") as exporter,
            patch.object(module_zones.messagebox, "showinfo") as info,
        ):
            frame._exporter_etude()
        exporter.assert_called_once_with(42, "/tmp/rhone.hydrok")
        info.assert_called_once()

    def test_export_annule_ne_fait_aucune_operation(self):
        frame = self._frame((42, (1, "Étude", "Site")))
        with (
            patch.object(module_zones.filedialog, "asksaveasfilename", return_value=""),
            patch.object(module_zones, "export_etude") as exporter,
        ):
            frame._exporter_etude()
        exporter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
