import tkinter as tk
import sqlite3

from repositories.zone_repository import ZoneRepository
from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository

from ui import theme
from utils.logging_config import obtenir_logger

logger = obtenir_logger(__name__)
from ui.widgets import (
    ScrollableFrame,
    HeaderBar,
    StatCard,
    bouton_primaire,
)


class HomeFrame(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent, bg=theme.BG)

        self.controller = controller

        self.zone_repo = ZoneRepository()
        self.point_repo = PointRepository()
        self.repetition_repo = RepetitionRepository()

        self.build_ui()

    # =====================================================
    # CONSTRUCTION
    # =====================================================

    def build_ui(self):
        header = HeaderBar(self, ["HydroK"])
        header.pack(fill="x")

        self.scrollable = ScrollableFrame(self, bg=theme.BG)
        self.scrollable.pack(fill="both", expand=True)

        contenu = tk.Frame(self.scrollable.contenu, bg=theme.BG)
        contenu.pack(fill="both", expand=True, padx=40, pady=36)

        self._bloc_hero(contenu)
        self._bloc_statistiques(contenu)
        self._bloc_navigation(contenu)
        self._bloc_pied_de_page(contenu)

    def nettoyer(self):
        self.scrollable.detruire_proprement()

    def refresh(self):
        self._charger_statistiques()

    # =====================================================
    # SECTIONS
    # =====================================================

    def _bloc_hero(self, parent):
        hero = tk.Frame(parent, bg=theme.BG)
        hero.pack(fill="x", pady=(0, 30))

        tk.Label(
            hero,
            text="HydroK",
            bg=theme.BG,
            fg=theme.PRIMARY,
            font=theme.f_h1(30),
        ).pack(anchor="w")

        tk.Label(
            hero,
            text="Suivi de terrain et calcul de conductivité hydraulique K",
            bg=theme.BG,
            fg=theme.TEXT_MUTED,
            font=theme.f_body(12),
        ).pack(anchor="w", pady=(4, 0))

    def _bloc_statistiques(self, parent):
        ligne = tk.Frame(parent, bg=theme.BG)
        ligne.pack(fill="x", pady=(0, 34))

        self.kpi_zones = StatCard(
            ligne, "Études", "—",
            "campagnes enregistrées", couleur=theme.PRIMARY
        )
        self.kpi_zones.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.kpi_points = StatCard(
            ligne, "Points de mesure", "—",
            "tous sites confondus", couleur=theme.ACCENT
        )
        self.kpi_points.pack(side="left", fill="x", expand=True, padx=12)

        self.kpi_repetitions = StatCard(
            ligne, "Répétitions saisies", "—",
            "mesures de terrain", couleur=theme.WARNING
        )
        self.kpi_repetitions.pack(side="left", fill="x", expand=True, padx=(12, 0))

        self._charger_statistiques()

    def _charger_statistiques(self):
        try:
            zones = self.zone_repo.lister()
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            logger.exception("Impossible de charger les statistiques d'accueil")
            zones = []

        nb_zones = len(zones)
        nb_points = sum(
            self.point_repo.compter_par_zone(z.id) for z in zones
        ) if zones else 0

        nb_repetitions = 0
        for z in zones:
            points_zone = self.point_repo.lister_par_zone(z.id)
            for p in points_zone:
                nb_repetitions += len(self.repetition_repo.lister_par_point(p.id))

        self.kpi_zones.maj_valeur(nb_zones)
        self.kpi_points.maj_valeur(nb_points)
        self.kpi_repetitions.maj_valeur(nb_repetitions)

    def _bloc_navigation(self, parent):
        tk.Label(
            parent,
            text="ACCÉDER À",
            bg=theme.BG,
            fg=theme.TEXT_MUTED,
            font=theme.f_label(9),
        ).pack(anchor="w", pady=(0, 10))

        ligne = tk.Frame(parent, bg=theme.BG)
        ligne.pack(fill="x")

        self._carte_navigation(
            ligne,
            titre="Gestion des études",
            description=(
                "Créer une étude, gérer ses points et saisir "
                "les répétitions de terrain. Accéder aux synthèses et "
                "statistiques de chaque étude."
            ),
            texte_bouton="Ouvrir les études  →",
            couleur=theme.PRIMARY,
            command=self.controller.show_zones,
        ).pack(side="left", fill="both", expand=True, padx=(0, 12))

        self._carte_navigation(
            ligne,
            titre="Gestion du matériel",
            description=(
                "Gérer le parc de sondes piézométriques et d'outils de "
                "mesure (entonnoirs, tuyaux) utilisés pour le calcul de K."
            ),
            texte_bouton="Ouvrir le matériel  →",
            couleur=theme.ACCENT,
            command=self.controller.show_materiel,
        ).pack(side="left", fill="both", expand=True, padx=(12, 0))

    def _carte_navigation(self, parent, titre, description, texte_bouton, couleur, command):
        carte = tk.Frame(
            parent,
            bg=theme.SURFACE,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
        )

        liseret = tk.Frame(carte, bg=couleur, height=4)
        liseret.pack(fill="x")

        corps = tk.Frame(carte, bg=theme.SURFACE)
        corps.pack(fill="both", expand=True, padx=22, pady=20)

        tk.Label(
            corps,
            text=titre,
            bg=theme.SURFACE,
            fg=theme.TEXT,
            font=theme.f_h3(14),
        ).pack(anchor="w")

        tk.Label(
            corps,
            text=description,
            bg=theme.SURFACE,
            fg=theme.TEXT_MUTED,
            font=theme.f_body(10),
            justify="left",
            wraplength=380,
        ).pack(anchor="w", pady=(8, 18))

        bouton = bouton_primaire(corps, texte_bouton, command=command)
        bouton.configure(bg=couleur)

        def on_enter(event):
            bouton.configure(bg=theme.PRIMARY_DARK if couleur == theme.PRIMARY else theme.ACCENT_DARK)

        def on_leave(event):
            bouton.configure(bg=couleur)

        bouton.bind("<Enter>", on_enter)
        bouton.bind("<Leave>", on_leave)
        bouton.pack(anchor="w")

        return carte

    def _bloc_pied_de_page(self, parent):
        tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", pady=(34, 14))

        tk.Label(
            parent,
            text="HydroK — Application de terrain pour le suivi de la conductivité hydraulique",
            bg=theme.BG,
            fg=theme.TEXT_FAINT,
            font=theme.f_small(9),
        ).pack(anchor="w")
