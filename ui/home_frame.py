import tkinter as tk
import sqlite3
from pathlib import Path

from PIL import Image, ImageTk

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
        self._bloc_fonctionnalites(contenu)
        self._bloc_navigation(contenu)
        self._bloc_limites(contenu)
        self._bloc_pied_de_page(contenu)

    def nettoyer(self):
        self.scrollable.detruire_proprement()

    def refresh(self):
        return

    # =====================================================
    # SECTIONS
    # =====================================================

    def _bloc_hero(self, parent):
        hero = tk.Frame(parent, bg=theme.BG)
        hero.pack(fill="x", pady=(0, 30))

        en_tete = tk.Frame(hero, bg=theme.BG)
        en_tete.pack(fill="x")

        chemin_logo = (
            Path(__file__).resolve().parent.parent
            / "assets" / "icone_hydrok.png"
        )
        with Image.open(chemin_logo) as image:
            self._logo_source = image.copy()
        filtre_logo = getattr(Image, "Resampling", Image).LANCZOS
        self._logo_tk = ImageTk.PhotoImage(
            self._logo_source.resize((80, 80), filtre_logo)
        )
        tk.Label(
            en_tete,
            image=self._logo_tk,
            bg=theme.BG,
            borderwidth=0,
            padx=0,
            pady=0,
        ).pack(side="left", anchor="n", padx=(0, 16))

        texte_en_tete = tk.Frame(en_tete, bg=theme.BG)
        texte_en_tete.pack(side="left", fill="x", expand=True)

        tk.Label(
            texte_en_tete,
            text="HydroK",
            bg=theme.BG,
            fg=theme.PRIMARY,
            font=theme.f_h1(30),
            anchor="w",
        ).pack(fill="x")

        sous_titre = tk.Label(
            texte_en_tete,
            text="Suivi de terrain et calcul de conductivité hydraulique K",
            bg=theme.BG,
            fg=theme.TEXT_MUTED,
            font=theme.f_body(12),
            anchor="w",
            justify="left",
            wraplength=500,
        )
        sous_titre.pack(fill="x", pady=(4, 0))

        def ajuster_sous_titre(evenement=None):
            sous_titre.configure(wraplength=max(120, texte_en_tete.winfo_width()))

        en_tete.bind("<Configure>", ajuster_sous_titre)

        banniere = tk.Frame(
            hero,
            bg=theme.SURFACE,
            height=130,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
        )
        banniere.pack(fill="x", pady=(16, 0))
        banniere.pack_propagate(False)
        image_banniere = tk.Label(
            banniere, bg=theme.SURFACE, borderwidth=0, padx=0, pady=0,
        )
        image_banniere.pack(expand=True)

        chemin_banniere = (
            Path(__file__).resolve().parent.parent
            / "assets" / "banniere_inrae.png"
        )
        with Image.open(chemin_banniere) as image:
            self._banniere_source = image.copy()
        self._banniere_tk = None
        self._banniere_dimensions = None
        self._banniere_redimensionnement_id = None

        def redimensionner_banniere():
            self._banniere_redimensionnement_id = None
            largeur_disponible = max(1, banniere.winfo_width() - 2)
            hauteur = max(120, min(210, round(largeur_disponible / 5.5)))
            banniere.configure(height=hauteur)
            hauteur_disponible = hauteur - 2
            dimensions = (largeur_disponible, hauteur_disponible)
            if dimensions == self._banniere_dimensions:
                return
            facteur = max(
                largeur_disponible / self._banniere_source.width,
                hauteur_disponible / self._banniere_source.height,
            )
            dimensions_redimensionnees = (
                max(1, round(self._banniere_source.width * facteur)),
                max(1, round(self._banniere_source.height * facteur)),
            )
            filtre = getattr(Image, "Resampling", Image).LANCZOS
            image = self._banniere_source.resize(
                dimensions_redimensionnees, filtre,
            )
            gauche = (image.width - largeur_disponible) // 2
            haut = (image.height - hauteur_disponible) // 2
            image = image.crop((
                gauche,
                haut,
                gauche + largeur_disponible,
                haut + hauteur_disponible,
            ))
            self._banniere_tk = ImageTk.PhotoImage(image)
            self._banniere_dimensions = dimensions
            image_banniere.configure(image=self._banniere_tk)

        def planifier_redimensionnement(evenement=None):
            if self._banniere_redimensionnement_id is not None:
                banniere.after_cancel(self._banniere_redimensionnement_id)
            self._banniere_redimensionnement_id = banniere.after(
                100, redimensionner_banniere,
            )

        banniere.bind("<Configure>", planifier_redimensionnement)

        presentation = tk.Frame(
            hero,
            bg=theme.SURFACE,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
        )
        presentation.pack(fill="x", pady=(18, 0))

        texte_presentation = tk.Label(
            presentation,
            text=(
                "HydroK est une application destinée à faciliter la saisie, "
                "le calcul et la visualisation des mesures de conductivité "
                "hydraulique réalisées sur le terrain.\n\n"
                "Elle permet d’organiser les mesures par étude et par point, "
                "de renseigner les répétitions et le matériel utilisé, de "
                "calculer automatiquement la conductivité hydraulique à partir "
                "des données saisies et de visualiser les résultats sous forme "
                "de tableaux, graphiques et cartes."
            ),
            bg=theme.SURFACE,
            fg=theme.TEXT,
            font=theme.f_body(10),
            justify="left",
            anchor="w",
        )
        texte_presentation.pack(fill="x", padx=22, pady=18)
        hero.bind(
            "<Configure>",
            lambda evenement: texte_presentation.configure(
                wraplength=max(200, evenement.width - 44)
            ),
        )

    def _bloc_fonctionnalites(self, parent):
        tk.Label(
            parent,
            text="Ce que permet HydroK",
            bg=theme.BG,
            fg=theme.TEXT,
            font=theme.f_h3(14),
        ).pack(anchor="w", pady=(0, 10))

        ligne = tk.Frame(parent, bg=theme.BG)
        ligne.pack(fill="x", pady=(0, 24))

        fonctionnalites = (
            "Organiser les études et les points de mesure",
            "Saisir les répétitions et le matériel",
            "Calculer automatiquement la conductivité hydraulique K",
            "Visualiser les résultats dans des tableaux, graphiques et cartes",
            "Exporter les résultats en CSV et PDF",
        )
        elements = []
        for fonctionnalite in fonctionnalites:
            element = tk.Label(
                ligne,
                text=f"•  {fonctionnalite}",
                bg=theme.BG,
                fg=theme.TEXT,
                font=theme.f_body(10),
                justify="left",
                anchor="w",
            )
            elements.append(element)

        etat = {"colonnes": None}

        def adapter_grille(evenement):
            largeur = evenement.width
            colonnes = 2 if largeur >= 760 else 1
            largeur_texte = max(180, largeur // colonnes - 24)
            for element in elements:
                element.configure(wraplength=largeur_texte)

            if colonnes == etat["colonnes"]:
                return
            etat["colonnes"] = colonnes
            for colonne in range(2):
                ligne.grid_columnconfigure(
                    colonne, weight=1 if colonne < colonnes else 0,
                )
            for index, element in enumerate(elements):
                element.grid_forget()
                element.grid(
                    row=index // colonnes,
                    column=index % colonnes,
                    sticky="ew",
                    padx=(0, 20),
                    pady=4,
                )

        ligne.bind("<Configure>", adapter_grille)

    def _bloc_statistiques(self, parent):
        ligne = tk.Frame(parent, bg=theme.BG)
        ligne.pack(fill="x", pady=(0, 34))

        self.kpi_zones = StatCard(
            ligne, "Études", "—",
            "campagnes enregistrées", couleur=theme.PRIMARY
        )
        self.kpi_zones.pack(side="left", fill="x", expand=True, padx=(0, 12))

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

        carte_etudes = self._carte_navigation(
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
        )

        carte_materiel = self._carte_navigation(
            ligne,
            titre="Gestion du matériel",
            description=(
                "Gérer le parc de sondes piézométriques et d'outils de "
                "mesure (entonnoirs, tuyaux) utilisés pour le calcul de K."
            ),
            texte_bouton="Ouvrir le matériel  →",
            couleur=theme.ACCENT,
            command=self.controller.show_materiel,
        )

        cartes = (carte_etudes, carte_materiel)
        etat = {"colonnes": None}

        def adapter_acces(evenement):
            colonnes = 2 if evenement.width >= 760 else 1
            if colonnes == etat["colonnes"]:
                return
            etat["colonnes"] = colonnes
            for colonne in range(2):
                ligne.grid_columnconfigure(
                    colonne, weight=1 if colonne < colonnes else 0,
                )
            for index, carte in enumerate(cartes):
                carte.grid_forget()
                carte.grid(
                    row=index // colonnes,
                    column=index % colonnes,
                    sticky="nsew",
                    padx=(0, 12) if colonnes == 2 and index == 0 else (
                        (12, 0) if colonnes == 2 else (0, 0)
                    ),
                    pady=(0, 12) if colonnes == 1 else (0, 0),
                )

        ligne.bind("<Configure>", adapter_acces)

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

        description_label = tk.Label(
            corps,
            text=description,
            bg=theme.SURFACE,
            fg=theme.TEXT_MUTED,
            font=theme.f_body(10),
            justify="left",
            wraplength=380,
        )
        description_label.pack(anchor="w", pady=(8, 18))
        carte.bind(
            "<Configure>",
            lambda evenement: description_label.configure(
                wraplength=max(180, evenement.width - 44)
            ),
        )

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

    def _bloc_limites(self, parent):
        bloc = tk.Frame(parent, bg=theme.BG)
        bloc.pack(fill="x", pady=(24, 0))

        tk.Frame(bloc, bg=theme.BORDER, height=1).pack(fill="x", pady=(0, 12))
        tk.Label(
            bloc,
            text="Limites",
            bg=theme.BG,
            fg=theme.TEXT_MUTED,
            font=theme.f_label(9),
        ).pack(anchor="w")
        texte = tk.Label(
            bloc,
            text=(
                "Les résultats dépendent de la qualité des données saisies. Le "
                "fond cartographique OpenStreetMap nécessite une connexion "
                "Internet lors de son chargement."
            ),
            bg=theme.BG,
            fg=theme.TEXT_FAINT,
            font=theme.f_small(9),
            justify="left",
            anchor="w",
        )
        texte.pack(fill="x", pady=(5, 0))
        bloc.bind(
            "<Configure>",
            lambda evenement: texte.configure(
                wraplength=max(200, evenement.width)
            ),
        )

    def _bloc_pied_de_page(self, parent):
        tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", pady=(34, 14))

        tk.Label(
            parent,
            text="HydroK — Application de terrain pour le suivi de la conductivité hydraulique",
            bg=theme.BG,
            fg=theme.TEXT_FAINT,
            font=theme.f_small(9),
        ).pack(anchor="w")
