"""Fenêtre principale et navigation de l'application HydroK."""

import tkinter as tk
from utils.logging_config import obtenir_logger
from ui.error_handler import afficher_erreur_inattendue

logger = obtenir_logger(__name__)

from ui import theme
from ui.home_frame import HomeFrame
from ui.zone_frame import ZoneFrame
from ui.point_frame import PointFrame
from ui.repetition_frame import RepetitionFrame
from ui.materiel_frame import MaterielFrame
from ui.maps import CarteInteractive
from ui.zone_synthese_frame import ZoneSyntheseFrame


class MainWindow:
    """Fenêtre principale de l'application."""

    LARGEUR_DEFAUT = 1280
    HAUTEUR_DEFAUT = 800

    def __init__(self):
        """Initialise la fenêtre principale."""
        self.root = tk.Tk()
        self._fermeture_en_cours = False
        self.root.report_callback_exception = self._gerer_exception_callback
        self.root.protocol("WM_DELETE_WINDOW", self.fermer)
        self.root.withdraw()
        self.root.title("HydroK — Conductivité Hydraulique")

        theme.apply_theme(self.root)

        self.root.minsize(900, 650)

        self.current_frame = None

        # Mémorise le contexte de navigation courant (zone / point ouverts)
        self.current_zone_id = None
        self.current_zone_nom = None
        self.current_point_id = None
        self.current_point_nom = None

        # Seules les pages de liste sont gardées pour rendre les retours rapides.
        self._cached_frames = {
            "home": None,
            "zones": None,
            "points": None,
            "materiel": None,
        }

        self.show_home()
        self._centrer_fenetre(self.LARGEUR_DEFAUT, self.HAUTEUR_DEFAUT)
        self.root.deiconify()

    # =====================================================
    # UTILITAIRES FENÊTRE
    # =====================================================
    def _gerer_exception_callback(self, exception_type, erreur, traceback):
        """Dernière frontière des callbacks Tkinter non traités localement."""
        if self._fermeture_en_cours:
            return
        logger.error(
            "Erreur inattendue dans un callback Tkinter",
            exc_info=(exception_type, erreur, traceback),
        )
        afficher_erreur_inattendue(self.root)

    def fermer(self):
        """Ferme une seule fois l'application après neutralisation des tâches Tk."""
        if self._fermeture_en_cours:
            return
        self._fermeture_en_cours = True
        self.root.withdraw()

        cartes = []

        def parcourir(widget):
            for enfant in widget.winfo_children():
                if isinstance(enfant, CarteInteractive):
                    cartes.append(enfant)
                parcourir(enfant)

        parcourir(self.root)
        for carte in cartes:
            carte.nettoyer_avant_fermeture()

        pages = {
            page for page in (
                self.current_frame,
                *self._cached_frames.values(),
            )
            if page is not None
        }
        for page in pages:
            nettoyer = getattr(page, "nettoyer", None)
            if callable(nettoyer):
                nettoyer()

        self.root.destroy()


    def _centrer_fenetre(self, largeur, hauteur):
        """Centre la fenêtre sur l'écran."""
        self.root.update_idletasks()
        ecran_largeur = self.root.winfo_screenwidth()
        ecran_hauteur = self.root.winfo_screenheight()

        x = max(0, (ecran_largeur - largeur) // 2)
        y = max(0, (ecran_hauteur - hauteur) // 3)

        self.root.geometry(f"{largeur}x{hauteur}+{x}+{y}")

    def clear_frame(self):
        """Supprime la page actuellement affichée."""
        if self.current_frame is not None:
            nettoyer = getattr(self.current_frame, "nettoyer", None)
            if callable(nettoyer):
                nettoyer()
            self.current_frame.destroy()
            self.current_frame = None

    def _is_cached_frame(self, frame):
        return frame is not None and frame in self._cached_frames.values()

    def _retire_frame(self, frame):
        if frame is None:
            return

        nettoyer = getattr(frame, "nettoyer", None)
        if callable(nettoyer):
            nettoyer()

        if not self._is_cached_frame(frame):
            frame.destroy()

    def _discard_cached_frame(self, key):
        frame = self._cached_frames.get(key)
        if frame is None:
            return

        self._cached_frames[key] = None
        if frame is self.current_frame:
            return

        nettoyer = getattr(frame, "nettoyer", None)
        if callable(nettoyer):
            nettoyer()
        frame.destroy()

    def invalidate_points_cache(self, zone_id=None):
        frame = self._cached_frames.get("points")
        if frame is None:
            return
        if zone_id is None or frame.zone_id == int(zone_id):
            self._discard_cached_frame("points")

    def _replace_frame(self, frame_factory):
        """
            Remplace la page affichée.

            L'ancienne page reste visible tant que la nouvelle n'est pas prête.
        """
        if self._fermeture_en_cours:
            return
        old_frame = self.current_frame
        children_before = set(self.root.winfo_children())

        try:
            new_frame = frame_factory()
        except Exception:
            # Frontière d'une navigation Tkinter : restaurer la page active puis remonter.
            logger.exception("Échec de construction d'une page")
            # On garde l'ancienne page si la construction de la nouvelle échoue.
            for child in self.root.winfo_children():
                if child not in children_before:
                    child.destroy()
            if old_frame is not None and old_frame.winfo_exists():
                old_frame.lift()
            raise

        try:
            new_frame.pack(fill="both", expand=True)
        except tk.TclError:
            logger.exception("Échec d'affichage d'une page")
            new_frame.destroy()
            if old_frame is not None and old_frame.winfo_exists():
                old_frame.lift()
            raise

        self.current_frame = new_frame

        if old_frame is None:
            return

        # On affiche la nouvelle page avant de retirer l'ancienne.
        new_frame.lift()
        old_frame.pack_forget()

        self._retire_frame(old_frame)

    def _show_cached_frame(self, key, frame_factory):
        if self._fermeture_en_cours:
            return
        frame = self._cached_frames.get(key)

        if frame is None:
            self._replace_frame(frame_factory)
            self._cached_frames[key] = self.current_frame
            return

        old_frame = self.current_frame

        refresh = getattr(frame, "refresh", None)
        if callable(refresh):
            refresh()

        if frame is old_frame:
            frame.lift()
            return

        frame.pack(fill="both", expand=True)
        frame.lift()
        self.current_frame = frame

        if old_frame is not None:
            old_frame.pack_forget()
            self._retire_frame(old_frame)

    def run(self):
        """Lance la boucle principale de Tkinter."""
        self.root.mainloop()

    # =====================================================
    # NAVIGATION
    # =====================================================

    def show_home(self):
        """Affiche la page d'accueil."""
        self._show_cached_frame("home", lambda: HomeFrame(
            parent=self.root,
            controller=self
        ))

    def show_zones(self):
        """Affiche la liste des zones."""
        self._show_cached_frame("zones", lambda: ZoneFrame(
            parent=self.root,
            controller=self
        ))

    def show_points(self, zone_id, zone_nom):
        """Affiche les points de mesure de la zone choisie."""
        cached_points = self._cached_frames.get("points")
        if cached_points is not None and cached_points.zone_id != int(zone_id):
            self._discard_cached_frame("points")

        self._show_cached_frame("points", lambda: PointFrame(
            parent=self.root,
            controller=self,
            zone_id=zone_id,
            zone_nom=zone_nom
        ))

        # Le contexte change seulement si la navigation a réussi.
        self.current_zone_id = zone_id
        self.current_zone_nom = zone_nom

    def show_repetitions(self, point_id, point_nom):
        """Affiche les répétitions du point choisi."""
        self._replace_frame(lambda: RepetitionFrame(
            parent=self.root,
            controller=self,
            point_id=point_id,
            point_nom=point_nom
        ))

        # Le contexte change seulement si la navigation a réussi.
        self.current_point_id = point_id
        self.current_point_nom = point_nom

    def show_materiel(self):
        """Affiche la page de gestion du matériel."""
        self._show_cached_frame("materiel", lambda: MaterielFrame(
            parent=self.root,
            controller=self
        ))

    def show_zone_synthese(self, zone_id, zone_nom):
        """Affiche la synthèse de la zone choisie."""
        self._replace_frame(lambda: ZoneSyntheseFrame(
            parent=self.root,
            controller=self,
            zone_id=zone_id,
            zone_nom=zone_nom
        ))
