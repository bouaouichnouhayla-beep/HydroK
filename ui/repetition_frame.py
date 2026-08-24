import tkinter as tk
import sqlite3
from utils.logging_config import obtenir_logger

logger = obtenir_logger(__name__)
from tkinter import ttk, messagebox

from repositories.repetition_repository import RepetitionRepository
from repositories.sonde_repository import SondeRepository
from repositories.point_repository import PointRepository
from ui.repetition_dialog import RepetitionDialog
from ui.error_handler import traiter_erreur_sqlite
from ui import theme, charts
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card, StatCard,
    bouton_primaire, bouton_secondaire, bouton_danger,
    configurer_zebrage, inserer_ligne,
)


class RepetitionFrame(tk.Frame):

    def __init__(self, parent, controller, point_id, point_nom):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller
        self.point_id = int(point_id)
        self.point_nom = point_nom

        self.repo = RepetitionRepository()
        self.point_repo = PointRepository()

        self.sonde_repo = SondeRepository()

        # Widgets KPI — conservés pour mise à jour
        self._kpi_widgets = []   # (StatCard, getter_func)
        self._chart_callback_ids = set()
        self._chart_futures = set()
        self._chart_generation = 0

        self._build()

    def nettoyer(self):
        self._annuler_rendus_graphiques()
        self.sf.detruire_proprement()

    # ------------------------------------------------------------------
    def _build(self):
        zone_id = getattr(self.controller, "current_zone_id", None)
        zone_nom = getattr(self.controller, "current_zone_nom", None) or "Étude"

        def retour_points():
            if zone_id is not None:
                self.controller.show_points(zone_id, zone_nom)

        HeaderBar(
            self,
            ["HydroK", "Études", zone_nom, self.point_nom, "Répétitions"],
            on_retour=retour_points
        ).pack(fill="x")

        self.sf = ScrollableFrame(self, bg=theme.BG)
        self.sf.pack(fill="both", expand=True)

        racine = tk.Frame(self.sf.contenu, bg=theme.BG)
        racine.pack(fill="both", expand=True, padx=36, pady=28)

        # Titre + bouton
        haut = tk.Frame(racine, bg=theme.BG)
        haut.pack(fill="x", pady=(0, 16))
        tk.Label(haut, text=f"Répétitions — {self.point_nom}",
                 bg=theme.BG, fg=theme.TEXT, font=theme.f_h1(20)).pack(side="left")
        bouton_primaire(haut, "+ Nouvelle répétition",
                        command=self._ouvrir_creation).pack(side="right", pady=4)

        # Cartes KPI (valeurs dynamiques)
        kpi_ligne = tk.Frame(racine, bg=theme.BG)
        kpi_ligne.pack(fill="x", pady=(0, 18))

        self.kpi_nb    = StatCard(kpi_ligne, "Répétitions", "—", "mesures saisies",
                                   couleur=theme.PRIMARY)
        self.kpi_moy   = StatCard(kpi_ligne, "K moyen", "—", "m/s",
                                   couleur=theme.ACCENT)
        self.kpi_min   = StatCard(kpi_ligne, "K min", "—", "m/s",
                                   couleur=theme.INFO)
        self.kpi_max   = StatCard(kpi_ligne, "K max", "—", "m/s",
                                   couleur=theme.WARNING)
        for kpi in (self.kpi_nb, self.kpi_moy, self.kpi_min, self.kpi_max):
            kpi.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Card tableau
        card = Card(racine, padding=0)
        card.pack(fill="both", expand=True)

        toolbar = tk.Frame(card.corps, bg=theme.SURFACE)
        toolbar.pack(fill="x", padx=16, pady=14)
        bouton_secondaire(toolbar, "✎  Modifier",
                          command=self._modifier).pack(side="left")
        bouton_danger(toolbar, "✕  Supprimer",
                      command=self._supprimer).pack(side="right")

        tk.Frame(card.corps, bg=theme.BORDER, height=1).pack(fill="x")

        cols = ("num", "profondeur", "ha", "hw", "temps", "volume",
                "methode", "sonde", "k_calcule")
        self.table = ttk.Treeview(card.corps, columns=cols,
                                  show="headings", selectmode="browse")
        configurer_zebrage(self.table)

        entetes = {
            "num":        ("Rép.",    55, "center"),
            "profondeur": ("h_p (cm)",  80, "center"),
            "ha":         ("h_a (cm)",  80, "center"),
            "hw":         ("h_w (cm)",  80, "center"),
            "temps":      ("Temps (s)", 90, "center"),
            "volume":     ("Vol. (L)",  90, "center"),
            "methode":    ("Méthode",  110, "center"),
            "sonde":      ("Sonde",    100, "center"),
            "k_calcule":  ("K calculé (m/s)", 150, "center"),
        }
        for col, (label, larg, anch) in entetes.items():
            self.table.heading(col, text=label)
            self.table.column(col, width=larg, anchor=anch, minwidth=40)

        vsb = ttk.Scrollbar(card.corps, orient="vertical",
                            command=self.table.yview)
        self.table.configure(yscrollcommand=vsb.set)

        self.table.pack(side="left", fill="both", expand=True,
                        padx=(16, 0), pady=(0, 16))
        vsb.pack(side="right", fill="y", pady=(0, 16), padx=(0, 6))

        self.graphiques = tk.Frame(racine, bg=theme.BG)
        self.graphiques.pack(fill="x", pady=(24, 0))

        self.charger_repetitions()

    # ------------------------------------------------------------------
    def _maj_kpi(self, reps):
        k_vals = [r.k_calcule for r in reps if r.k_calcule is not None]
        self.kpi_nb.maj_valeur(len(reps))
        self.kpi_moy.maj_valeur(theme.format_k(
            sum(k_vals) / len(k_vals) if k_vals else None))
        self.kpi_min.maj_valeur(theme.format_k(min(k_vals) if k_vals else None))
        self.kpi_max.maj_valeur(theme.format_k(max(k_vals) if k_vals else None))

    # ------------------------------------------------------------------
    def charger_repetitions(self):
        for row in self.table.get_children():
            self.table.delete(row)

        reps = self.repo.lister_par_point(self.point_id)

        #Dictionnaire id -> nom de sonde
        sondes = {s.id: s.nom for s in self.sonde_repo.lister()}

        # Détection valeurs aberrantes (Tukey IQR sur k_calcule)
        k_vals = sorted(r.k_calcule for r in reps if r.k_calcule is not None)
        aberrantes_ids = set()
        if len(k_vals) >= 4:
            q1 = k_vals[len(k_vals) // 4]
            q3 = k_vals[(3 * len(k_vals)) // 4]
            iqr = q3 - q1
            borne_basse = q1 - 1.5 * iqr
            borne_haute = q3 + 1.5 * iqr
            for r in reps:
                if r.k_calcule is not None:
                    if r.k_calcule < borne_basse or r.k_calcule > borne_haute:
                        aberrantes_ids.add(r.id)

        for i, rep in enumerate(reps):
            inserer_ligne(
                self.table, i, str(rep.id),
                (i + 1,
                 theme.format_cm(rep.profondeur_enfoncement),
                 theme.format_cm(rep.hauteur_air),
                 theme.format_cm(rep.hauteur_eau),
                 rep.temps_infiltration,
                 rep.volume_eau,
                 rep.methode or "—",
                 sondes.get(rep.sonde_id, "-"),
                 theme.format_k(rep.k_calcule)),
                aberrante=rep.id in aberrantes_ids,
            )

        self._maj_kpi(reps)
        self._rafraichir_graphiques(reps)

    def _rafraichir_graphiques(self, reps):
        """Reconstruit les deux graphiques à partir de la liste actualisée."""
        self._annuler_rendus_graphiques()
        for widget in self.graphiques.winfo_children():
            widget.destroy()

        repetitions_par_profondeur = {}
        for rep in reps:
            if rep.profondeur_enfoncement is None or rep.k_calcule is None:
                continue
            profondeur_cm = round(rep.profondeur_enfoncement * 100.0, 6)
            repetitions_par_profondeur.setdefault(
                profondeur_cm, []
            ).append(rep.k_calcule)

        k_vals = [rep.k_calcule for rep in reps if rep.k_calcule is not None]
        titre_histo = (
            "Distribution de la conductivité hydraulique K "
            f"— Point {self.point_nom}"
        )

        tk.Label(
            self.graphiques, text="Graphiques",
            bg=theme.BG, fg=theme.TEXT, font=theme.f_h3(13),
        ).pack(anchor="w")
        tk.Frame(
            self.graphiques, bg=theme.BORDER, height=1
        ).pack(fill="x", pady=(4, 8))

        emplacement_profondeurs = self._creer_emplacement_graphique(380)
        self._demarrer_rendu_png(
            emplacement_profondeurs,
            lambda: charts.graphique_repetitions_par_profondeur(
                repetitions_par_profondeur, figsize=(9.0, 3.8)
            ),
        )

        emplacement_histo = self._creer_emplacement_graphique(320)
        self._demarrer_rendu_png(
            emplacement_histo,
            lambda: charts.graphique_histogramme(
                k_vals, figsize=(9.0, 3.2), titre=titre_histo
            ),
        )

    def _creer_emplacement_graphique(self, hauteur):
        emplacement = tk.Frame(
            self.graphiques, bg=theme.SURFACE, height=hauteur
        )
        emplacement.pack(fill="x", pady=(0, 20))
        emplacement.pack_propagate(False)
        return emplacement

    def _demarrer_rendu_png(self, emplacement, figure_factory):
        generation = self._chart_generation
        future = charts.soumettre_rendu_figure_png(figure_factory)
        self._chart_futures.add(future)
        callback_state = {}

        def verifier_resultat():
            callback_id = callback_state["id"]
            self._chart_callback_ids.discard(callback_id)

            if generation != self._chart_generation or not self.winfo_exists():
                future.cancel()
                self._chart_futures.discard(future)
                return
            if not emplacement.winfo_exists():
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
                    emplacement, image=photo,
                    bg=theme.SURFACE, bd=0, highlightthickness=0,
                )
                label.image = photo
                label.pack(fill="both", expand=True)
            except Exception:
                # Frontière d'un résultat asynchrone : le tableau reste disponible.
                logger.exception("Échec du rendu asynchrone d'un graphique")
                if emplacement.winfo_exists():
                    tk.Label(
                        emplacement,
                        text="Ce graphique n'a pas pu être généré.",
                        bg=theme.SURFACE,
                        fg=theme.TEXT_FAINT,
                        font=theme.f_small_italic(9),
                    ).pack(expand=True)

        def planifier_verification():
            callback_id = self.after(10, verifier_resultat)
            callback_state["id"] = callback_id
            self._chart_callback_ids.add(callback_id)

        planifier_verification()

    def _annuler_rendus_graphiques(self):
        self._chart_generation += 1
        for callback_id in list(self._chart_callback_ids):
            try:
                self.after_cancel(callback_id)
            except tk.TclError:
                logger.warning("Rappel de graphique déjà supprimé")
        self._chart_callback_ids.clear()
        for future in list(self._chart_futures):
            future.cancel()
        self._chart_futures.clear()

    def _selection(self):
        sel = self.table.selection()
        if not sel:
            return None
        return int(sel[0])

    # ------------------------------------------------------------------
    def _ouvrir_creation(self):
        RepetitionDialog(parent=self, point_id=self.point_id,
                         refresh_callback=self.charger_repetitions)

    def _modifier(self):
        rid = self._selection()
        if rid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une répétition.")
            return
        rep = self.repo.trouver_par_id(rid)
        if rep:
            RepetitionDialog(parent=self, point_id=self.point_id,
                             refresh_callback=self.charger_repetitions,
                             repetition=rep)

    def _supprimer(self):
        rid = self._selection()
        if rid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une répétition.")
            return
        if messagebox.askyesno("Supprimer", "Supprimer cette répétition ?"):
            try:
                self.repo.supprimer(rid)
            except (sqlite3.IntegrityError, sqlite3.OperationalError,
                    sqlite3.DatabaseError) as erreur:
                traiter_erreur_sqlite(erreur, self, "la suppression de la répétition")
                return
            self.charger_repetitions()
