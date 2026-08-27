"""
Page de synthèse d'une zone de mesure.
Affiche : KPI, tableau récapitulatif par point,
histogramme de distribution, dispersion et camembert des faciès.
"""
import statistics
import tkinter as tk
from tkinter import ttk

from repositories.zone_repository import ZoneRepository
from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository
from services.synthese_table_service import SyntheseTableService
from ui import theme, charts
from ui.maps import CarteInteractive, PointCarte
from ui.synthese_tables import afficher_materiels_etude, afficher_repetitions
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card, StatCard,
    configurer_zebrage, inserer_ligne, EmptyState,
    bouton_secondaire,
)
from utils.logging_config import obtenir_logger

logger = obtenir_logger(__name__)

try:
    from ui.charts import inserer_figure
    _CHARTS_OK = True
except (ImportError, RuntimeError):
    _CHARTS_OK = False


class ZoneSyntheseFrame(tk.Frame):

    def __init__(self, parent, controller, zone_id, zone_nom):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller
        self.zone_id = int(zone_id)
        self.zone_nom = zone_nom

        self.zone_repo = ZoneRepository()
        self.point_repo = PointRepository()
        self.repetition_repo = RepetitionRepository()
        self.synthese_table_service = SyntheseTableService()
        self.zone = self.zone_repo.trouver_par_id(self.zone_id)

        self._chart_tasks = []
        self._chart_callback_ids = set()
        self._chart_futures = set()
        self.carte_interactive = None

        self._build()

    def nettoyer(self):
        for callback_id in list(self._chart_callback_ids):
            try:
                self.after_cancel(callback_id)
            except tk.TclError:
                logger.warning("Rappel de graphique déjà supprimé")
        self._chart_callback_ids.clear()
        self._chart_tasks.clear()
        for future in list(self._chart_futures):
            future.cancel()
        self._chart_futures.clear()
        if self.carte_interactive is not None:
            self.carte_interactive.destroy()
            self.carte_interactive = None
        self.sf.detruire_proprement()

    # ------------------------------------------------------------------
    def _build(self):
        def retour():
            self.controller.show_zones()

        HeaderBar(
            self,
            ["HydroK", "Études", self.zone_nom, "Synthèse"],
            on_retour=retour,
        ).pack(fill="x")

        self.sf = ScrollableFrame(self, bg=theme.BG)
        self.sf.pack(fill="both", expand=True)

        racine = tk.Frame(self.sf.contenu, bg=theme.BG)
        racine.pack(fill="both", expand=True, padx=36, pady=28)

        # Titre
        tk.Label(racine, text=f"Synthèse de l'étude — {self.zone_nom}",
                 bg=theme.BG, fg=theme.TEXT, font=theme.f_h1(22)).pack(anchor="w")

        if self.zone:
            tk.Label(
                racine,
                text=f"{self.zone.site}  ·  {self.zone.date_campagne}  ·  {self.zone.operateur}",
                bg=theme.BG, fg=theme.TEXT_MUTED, font=theme.f_body(10),
            ).pack(anchor="w", pady=(4, 0))

        # ------ Données ------
        points = self.point_repo.lister_par_zone(self.zone_id)
        reps_zone = []
        for p in points:
            reps_zone.extend(self.repetition_repo.lister_par_point(p.id))

        nb_pts = len(points)
        nb_reps = len(reps_zone)
        k_vals_zone = [r.k_calcule for r in reps_zone if r.k_calcule is not None]
        k_moy_zone = statistics.mean(k_vals_zone) if k_vals_zone else None
        k_std_zone = statistics.stdev(k_vals_zone) if len(k_vals_zone) > 1 else None
        k_min_zone = min(k_vals_zone) if k_vals_zone else None
        k_max_zone = max(k_vals_zone) if k_vals_zone else None
        donnees_tableaux = self.synthese_table_service.pour_zone(self.zone_id)

        # ------ KPI ------
        kpi_ligne = tk.Frame(racine, bg=theme.BG)
        kpi_ligne.pack(fill="x", pady=(20, 24))

        for titre, valeur, stxt, couleur in [
            ("K moyen étude",   theme.format_k(k_moy_zone),  "m/s",         theme.PRIMARY),
            ("K min",           theme.format_k(k_min_zone),  "m/s",         theme.INFO),
            ("K max",           theme.format_k(k_max_zone),  "m/s",         theme.WARNING),
            ("Points",          nb_pts,                       "points",      theme.ACCENT),
            ("Répétitions",     nb_reps,                      "mesures",     theme.TEXT_MUTED),
        ]:
            StatCard(kpi_ligne, titre, valeur, stxt,
                     couleur=couleur).pack(side="left", fill="x", expand=True, padx=(0, 10))

        # ------ Tableau récap par point ------
        self._section(racine, "Tableau récapitulatif par point")
        card_table = Card(racine, padding=0)
        card_table.pack(fill="x", pady=(8, 24))

        cols = ("nom", "facies", "nb_rep", "k_moy", "k_min", "k_max", "k_std", "profondeurs")
        table = ttk.Treeview(card_table.corps, columns=cols, show="headings", height=min(nb_pts + 1, 12))
        configurer_zebrage(table)

        for col, label, w in [
            ("nom",        "Point",            130),
            ("facies",     "Faciès",           100),
            ("nb_rep",     "Rép.",              55),
            ("k_moy",      "K moyen (m/s)",    140),
            ("k_min",      "K min (m/s)",      130),
            ("k_max",      "K max (m/s)",      130),
            ("k_std",      "Écart-type",        110),
            ("profondeurs","Profondeurs (cm)",   160),
        ]:
            table.heading(col, text=label)
            table.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(card_table.corps, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=vsb.set)
        table.pack(side="left", fill="x", expand=True, padx=(14, 0), pady=(0, 14))
        vsb.pack(side="right", fill="y", pady=(0, 14), padx=(0, 6))

        # Données tableau
        pt_data = []
        for i, p in enumerate(points):
            reps_pt = self.repetition_repo.lister_par_point(p.id)
            k_pt = [r.k_calcule for r in reps_pt if r.k_calcule is not None]
            k_m = statistics.mean(k_pt) if k_pt else None
            k_n = min(k_pt) if k_pt else None
            k_x = max(k_pt) if k_pt else None
            k_s = statistics.stdev(k_pt) if len(k_pt) > 1 else None
            prof = theme.format_profondeurs_cm(
                self.repetition_repo.profondeurs_par_point(p.id) or "—")

            pt_data.append({
                "point": p, "k_vals": k_pt,
                "k_moy": k_m, "k_min": k_n, "k_max": k_x,
            })

            inserer_ligne(table, i, str(p.id), (
                p.nom, p.facies,
                len(reps_pt),
                theme.format_k(k_m),
                theme.format_k(k_n),
                theme.format_k(k_x),
                theme.format_k(k_s),
                prof,
            ))

        points_carte = [
            PointCarte(
                nom=d["point"].nom,
                latitude=d["point"].latitude,
                longitude=d["point"].longitude,
                facies=d["point"].facies,
                k_moyen=d["k_moy"],
            )
            for d in pt_data
        ]
        self._section(racine, "Localisation des points de mesure")
        self._ajouter_carte_interactive(racine, points_carte)

        self._section(racine, "Détail des points et répétitions")
        afficher_repetitions(
            racine, donnees_tableaux.repetitions, afficher_point=True
        )

        self._section(racine, "Matériel utilisé")
        afficher_materiels_etude(racine, donnees_tableaux.materiels)

        # ------ Graphiques ------
        if _CHARTS_OK and points:
            self._section(racine, "Graphiques statistiques")

            grille_graphiques = tk.Frame(racine, bg=theme.BG)
            grille_graphiques.pack(fill="x", pady=(8, 24))
            emplacements_graphiques = []

            def ajouter_graphique(fabrique):
                emplacement = self._creer_emplacement_graphique(
                    grille_graphiques, 320
                )
                emplacements_graphiques.append(emplacement)
                self._chart_tasks.append((emplacement, fabrique))

            noms = [d["point"].nom for d in pt_data]
            valeurs_par_point = [d["k_vals"] for d in pt_data]

            # Camembert faciès
            facies_count = {}
            for d in pt_data:
                f = d["point"].facies or "—"
                facies_count[f] = facies_count.get(f, 0) + 1

            ajouter_graphique(
                lambda: charts.graphique_repartition_facies(
                    list(facies_count.keys()),
                    list(facies_count.values()),
                    figsize=(5.4, 3.2),
                ),
            )

            # Histogramme global K
            if len(k_vals_zone) >= 2:
                ajouter_graphique(
                    lambda: charts.graphique_histogramme(
                        k_vals_zone, figsize=(5.4, 3.2),
                        titre="Distribution des valeurs de K",
                    ),
                )

            # Boxplot des K par point
            if any(valeurs_par_point):
                ajouter_graphique(
                    lambda: charts.graphique_boxplot_k_par_point(
                        noms, valeurs_par_point, figsize=(5.4, 3.2),
                    ),
                )

            methodes_count = {}
            profondeurs_count = {}
            for rep in reps_zone:
                methode = rep.methode or "—"
                methodes_count[methode] = methodes_count.get(methode, 0) + 1

                if rep.profondeur_enfoncement is not None:
                    prof_cm = round(rep.profondeur_enfoncement * 100, 2)
                    profondeurs_count[prof_cm] = profondeurs_count.get(prof_cm, 0) + 1

            if methodes_count:
                ajouter_graphique(
                    lambda: charts.graphique_repartition_methodes(
                        list(methodes_count.keys()),
                        list(methodes_count.values()),
                        figsize=(5.4, 3.2),
                    ),
                )

            if profondeurs_count:
                profondeurs_ordonnees = sorted(profondeurs_count.keys())
                ajouter_graphique(
                    lambda: charts.graphique_repartition_profondeurs(
                        profondeurs_ordonnees,
                        [profondeurs_count[p] for p in profondeurs_ordonnees],
                        figsize=(5.4, 3.2),
                    ),
                )

            disposition_graphiques = {"colonnes": None}

            def adapter_grille(event):
                colonnes = 2 if event.width >= 900 else 1
                if disposition_graphiques["colonnes"] == colonnes:
                    return
                disposition_graphiques["colonnes"] = colonnes
                grille_graphiques.columnconfigure(0, weight=1)
                grille_graphiques.columnconfigure(
                    1, weight=1 if colonnes == 2 else 0
                )
                for index, emplacement in enumerate(emplacements_graphiques):
                    emplacement.grid_forget()
                    derniere_impaire = (
                        colonnes == 2
                        and index == len(emplacements_graphiques) - 1
                        and len(emplacements_graphiques) % 2 == 1
                    )
                    if colonnes == 1 or derniere_impaire:
                        marge_horizontale = 0
                    elif index % 2 == 0:
                        marge_horizontale = (0, 6)
                    else:
                        marge_horizontale = (6, 0)
                    emplacement.grid(
                        row=index // colonnes,
                        column=index % colonnes,
                        columnspan=2 if derniere_impaire else 1,
                        sticky="nsew",
                        padx=marge_horizontale,
                        pady=6,
                    )

            grille_graphiques.bind("<Configure>", adapter_grille)

        elif not points:
            EmptyState(
                racine,
                icone="📍",
                titre="Aucun point de mesure",
                sous_texte="Ajoutez des points à cette étude pour voir les statistiques.",
            ).pack(fill="x", pady=20)

        # ------ Bouton retour ------
        tk.Frame(racine, bg=theme.BORDER, height=1).pack(fill="x", pady=(10, 16))
        bouton_secondaire(racine, "← Retour aux études",
                          command=self.controller.show_zones).pack(anchor="w")

        if self._chart_tasks:
            self._planifier_prochain_graphique(idle=True)

    def _creer_emplacement_graphique(self, parent, hauteur):
        emplacement = tk.Frame(parent, bg=theme.SURFACE, height=hauteur)
        emplacement.pack_propagate(False)
        return emplacement

    def _ajouter_carte_interactive(self, parent, points):
        """Ajoute la carte en pleine largeur et lui transmet les points."""
        self.carte_interactive = CarteInteractive(parent, hauteur=480)
        self.carte_interactive.pack(fill="x", pady=(8, 24))
        self.carte_interactive.actualiser(points)

    def _planifier_prochain_graphique(self, idle=False):
        if not self._chart_tasks or not self.winfo_exists():
            return

        callback_state = {}

        def executer():
            callback_id = callback_state["id"]
            self._chart_callback_ids.discard(callback_id)

            if not self.winfo_exists() or not self._chart_tasks:
                return

            emplacement, figure_factory = self._chart_tasks.pop(0)
            self._demarrer_rendu_png(emplacement, figure_factory)

        if idle:
            callback_id = self.after_idle(executer)
        else:
            callback_id = self.after(10, executer)

        callback_state["id"] = callback_id
        self._chart_callback_ids.add(callback_id)

    def _demarrer_rendu_png(self, emplacement, figure_factory):
        if not self.winfo_exists() or not emplacement.winfo_exists():
            return

        future = charts.soumettre_rendu_figure_png(figure_factory)
        self._chart_futures.add(future)

        def verifier_resultat():
            callback_id = callback_state["id"]
            self._chart_callback_ids.discard(callback_id)

            if not self.winfo_exists() or not emplacement.winfo_exists():
                future.cancel()
                self._chart_futures.discard(future)
                return

            if not future.done():
                planifier_verification()
                return

            self._chart_futures.discard(future)

            try:
                png_data = future.result()
                photo = tk.PhotoImage(data=png_data, format="png")
                label = tk.Label(
                    emplacement,
                    image=photo,
                    bg=theme.SURFACE,
                    bd=0,
                    highlightthickness=0,
                )
                label.image = photo
                label.pack(fill="both", expand=True)
            except Exception:
                # Frontière d'un résultat asynchrone : conserver la synthèse affichée.
                logger.exception("Échec du rendu asynchrone d'un graphique")
                if self.winfo_exists() and emplacement.winfo_exists():
                    tk.Label(
                        emplacement,
                        text="Ce graphique n'a pas pu être généré.",
                        bg=theme.SURFACE,
                        fg=theme.TEXT_FAINT,
                        font=theme.f_small_italic(9),
                    ).pack(expand=True)
            finally:
                if self._chart_tasks and self.winfo_exists():
                    self._planifier_prochain_graphique()

        def planifier_verification():
            callback_id = self.after(10, verifier_resultat)
            callback_state["id"] = callback_id
            self._chart_callback_ids.add(callback_id)

        callback_state = {}
        planifier_verification()

    def _rendre_graphique(self, emplacement, figure_factory):
        if not self.winfo_exists() or not emplacement.winfo_exists():
            return

        try:
            figure = figure_factory()

            if not self.winfo_exists() or not emplacement.winfo_exists():
                return

            widget = inserer_figure(emplacement, figure)
            widget.pack(fill="both", expand=True)
        except Exception:
            # Frontière du composant graphique optionnel.
            logger.exception("Échec du rendu d'un graphique")
            if self.winfo_exists() and emplacement.winfo_exists():
                tk.Label(
                    emplacement,
                    text="Ce graphique n'a pas pu être généré.",
                    bg=theme.SURFACE,
                    fg=theme.TEXT_FAINT,
                    font=theme.f_small_italic(9),
                ).pack(expand=True)

    def _section(self, parent, titre):
        tk.Label(parent, text=titre,
                 bg=theme.BG, fg=theme.TEXT,
                 font=theme.f_h3(13)).pack(anchor="w")
        tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", pady=(4, 0))
