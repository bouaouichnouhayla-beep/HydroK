"""Tests de la fermeture coordonnée de la fenêtre principale."""

import unittest
from unittest.mock import Mock, patch

import ui.main_window as module_fenetre
from ui.main_window import MainWindow


class FauxWidget:
    def __init__(self, enfants=None):
        self.enfants = list(enfants or [])

    def winfo_children(self):
        return list(self.enfants)


class FausseCarte(FauxWidget):
    def __init__(self):
        super().__init__()
        self.nettoyer_avant_fermeture = Mock()


class FausseRacine(FauxWidget):
    def __init__(self, enfants=None):
        super().__init__(enfants)
        self.withdraw = Mock()
        self.destroy = Mock()
        self.protocol = Mock()


class AppShutdownTest(unittest.TestCase):

    @staticmethod
    def _fenetre(racine, page=None, pages_cachees=None):
        fenetre = MainWindow.__new__(MainWindow)
        fenetre.root = racine
        fenetre._fermeture_en_cours = False
        fenetre.current_frame = page
        fenetre._cached_frames = pages_cachees or {
            "home": None, "zones": None, "points": None, "materiel": None,
        }
        return fenetre

    def test_fermeture_depuis_une_page_avec_plusieurs_cartes(self):
        carte_1 = FausseCarte()
        carte_2 = FausseCarte()
        page = FauxWidget([FauxWidget([carte_1]), carte_2])
        page.nettoyer = Mock()
        racine = FausseRacine([page])
        fenetre = self._fenetre(racine, page, {"points": page})

        with patch.object(module_fenetre, "CarteInteractive", FausseCarte):
            fenetre.fermer()
            fenetre.fermer()

        carte_1.nettoyer_avant_fermeture.assert_called_once_with()
        carte_2.nettoyer_avant_fermeture.assert_called_once_with()
        page.nettoyer.assert_called_once_with()
        racine.withdraw.assert_called_once_with()
        racine.destroy.assert_called_once_with()

    def test_fermeture_depuis_une_page_sans_carte(self):
        page = FauxWidget()
        page.nettoyer = Mock()
        racine = FausseRacine([page])
        fenetre = self._fenetre(racine, page)

        with patch.object(module_fenetre, "CarteInteractive", FausseCarte):
            fenetre.fermer()

        page.nettoyer.assert_called_once_with()
        racine.withdraw.assert_called_once_with()
        racine.destroy.assert_called_once_with()

    def test_navigation_et_rafraichissement_bloques_pendant_fermeture(self):
        racine = FausseRacine()
        fenetre = self._fenetre(racine)
        fenetre._fermeture_en_cours = True
        fabrique = Mock()

        fenetre._replace_frame(fabrique)
        fenetre._show_cached_frame("points", fabrique)

        fabrique.assert_not_called()


if __name__ == "__main__":
    unittest.main()
