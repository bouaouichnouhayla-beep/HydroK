"""
Page de synthèse d'un point de mesure.
Affiche les indicateurs statistiques et les tableaux détaillés du point.
"""
import statistics
import tkinter as tk
from tkinter import ttk

from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository
from services.synthese_table_service import SyntheseTableService
from ui import theme
from ui.synthese_tables import afficher_materiels, afficher_repetitions
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card, StatCard,
    configurer_zebrage, inserer_ligne, EmptyState,
    bouton_secondaire,
)

class PointSyntheseFrame(tk.Frame):

    def __init__(self, parent, controller, point_id, point_nom):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller
        self.point_id = int(point_id)
        self.point_nom = point_nom

        self.point_repo = PointRepository()
        self.repetition_repo = RepetitionRepository()
        self.synthese_table_service = SyntheseTableService()
        self.point = self.point_repo.trouver_par_id(self.point_id)

        self._build()

    def nettoyer(self):
        self.sf.detruire_proprement()

    # ------------------------------------------------------------------
    def _build(self):
        zone_nom = getattr(self.controller, "current_zone_nom", None) or "Étude"
        zone_id  = getattr(self.controller, "current_zone_id", None)

        def retour_points():
            if zone_id is not None:
                self.controller.show_points(zone_id, zone_nom)

        HeaderBar(
            self,
            ["HydroK", "Études", zone_nom, self.point_nom, "Synthèse"],
            on_retour=retour_points,
        ).pack(fill="x")

        self.sf = ScrollableFrame(self, bg=theme.BG)
        self.sf.pack(fill="both", expand=True)

        racine = tk.Frame(self.sf.contenu, bg=theme.BG)
        racine.pack(fill="both", expand=True, padx=36, pady=28)

        # Titre
        tk.Label(racine, text=f"Synthèse — {self.point_nom}",
                 bg=theme.BG, fg=theme.TEXT, font=theme.f_h1(22)).pack(anchor="w")

        if self.point:
            infos = []
            if self.point.facies:
                infos.append(f"Faciès : {self.point.facies}")
            if self.point.latitude is not None:
                infos.append(f"N {self.point.latitude}")
            if self.point.longitude is not None:
                infos.append(f"E {self.point.longitude}")
            tk.Label(
                racine, text="  ·  ".join(infos) if infos else "",
                bg=theme.BG, fg=theme.TEXT_MUTED, font=theme.f_body(10),
            ).pack(anchor="w", pady=(4, 0))

        # ------ Données ------
        reps = self.repetition_repo.lister_par_point(self.point_id)
        k_vals = [r.k_calcule for r in reps if r.k_calcule is not None]
        k_moy  = statistics.mean(k_vals)  if k_vals          else None
        k_std  = statistics.stdev(k_vals) if len(k_vals) > 1 else None
        k_min  = min(k_vals)              if k_vals          else None
        k_max  = max(k_vals)              if k_vals          else None
        nb_reps = len(reps)
        donnees_tableaux = self.synthese_table_service.pour_point(self.point_id)

        # Détection aberrantes (Tukey IQR)
        aberrantes_ids = set()
        if len(k_vals) >= 4:
            ks = sorted(k_vals)
            q1 = ks[len(ks) // 4]
            q3 = ks[(3 * len(ks)) // 4]
            iqr = q3 - q1
            bb, bh = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            for r in reps:
                if r.k_calcule is not None and (r.k_calcule < bb or r.k_calcule > bh):
                    aberrantes_ids.add(r.id)
        nb_aberrantes = len(aberrantes_ids)

        # ------ KPI ------
        kpi_ligne = tk.Frame(racine, bg=theme.BG)
        kpi_ligne.pack(fill="x", pady=(20, 24))

        for titre, valeur, stxt, couleur in [
            ("K moyen",       theme.format_k(k_moy), "m/s",      theme.PRIMARY),
            ("K min",         theme.format_k(k_min), "m/s",      theme.INFO),
            ("K max",         theme.format_k(k_max), "m/s",      theme.WARNING),
            ("Écart-type",    theme.format_k(k_std), "m/s",      theme.ACCENT),
            ("Répétitions",   nb_reps,               "mesures",  theme.TEXT_MUTED),
            ("Aberrantes",    nb_aberrantes,          "valeurs",  theme.DANGER if nb_aberrantes else theme.SUCCESS),
        ]:
            StatCard(kpi_ligne, titre, valeur, stxt,
                     couleur=couleur).pack(side="left", fill="x", expand=True, padx=(0, 8))

        # ------ Tableau des répétitions ------
        self._section(racine, "Détail des répétitions")
        card_table = Card(racine, padding=0)
        card_table.pack(fill="x", pady=(8, 24))

        cols = ("num", "profondeur", "ha", "hw", "temps",
                "volume", "methode", "k_calcule", "aberrante")
        table = ttk.Treeview(card_table.corps, columns=cols,
                             show="headings", height=min(nb_reps + 1, 10))
        configurer_zebrage(table)

        for col, label, w in [
            ("num",        "Rép.",        55),
            ("profondeur", "h_p (cm)",      80),
            ("ha",         "h_a (cm)",      80),
            ("hw",         "h_w (cm)",      80),
            ("temps",      "Temps (s)",    90),
            ("volume",     "Vol. (L)",     90),
            ("methode",    "Méthode",     110),
            ("k_calcule",  "K (m/s)",     145),
            ("aberrante",  "Statut",       80),
        ]:
            table.heading(col, text=label)
            table.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(card_table.corps, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=vsb.set)
        table.pack(side="left", fill="x", expand=True, padx=(14, 0), pady=(0, 14))
        vsb.pack(side="right", fill="y", pady=(0, 14), padx=(0, 6))

        for i, rep in enumerate(reps):
            ab = rep.id in aberrantes_ids
            inserer_ligne(table, i, str(rep.id), (
                i + 1,
                theme.format_cm(rep.profondeur_enfoncement),
                theme.format_cm(rep.hauteur_air),
                theme.format_cm(rep.hauteur_eau),
                rep.temps_infiltration,
                rep.volume_eau,
                rep.methode or "—",
                theme.format_k(rep.k_calcule),
                "⚠ Aberrante" if ab else "OK",
            ), aberrante=ab)

        self._section(racine, "Données détaillées pour l'export")
        afficher_repetitions(
            racine, donnees_tableaux.repetitions,
            aberrantes_ids=aberrantes_ids,
        )

        self._section(racine, "Matériel utilisé")
        afficher_materiels(racine, donnees_tableaux.materiels)

        # ------ Remarque sur aberrantes ------
        if nb_aberrantes:
            tk.Label(
                racine,
                text=(f"⚠  {nb_aberrantes} valeur(s) aberrante(s) détectée(s) "
                      "(méthode Tukey — IQR × 1,5). Elles sont exclues du calcul de K moyen recommandé."),
                bg=theme.WARNING_BG, fg=theme.WARNING,
                font=theme.f_small(9),
                padx=14, pady=8,
                justify="left",
            ).pack(fill="x", pady=(0, 16))

        if not reps:
            EmptyState(
                racine,
                icone="📏",
                titre="Aucune répétition saisie",
                sous_texte="Saisissez des répétitions pour ce point pour voir les statistiques.",
            ).pack(fill="x", pady=20)

        # ------ Bouton retour ------
        tk.Frame(racine, bg=theme.BORDER, height=1).pack(fill="x", pady=(10, 16))
        bouton_secondaire(racine, "← Retour aux points",
                          command=retour_points).pack(anchor="w")

    def _section(self, parent, titre):
        tk.Label(parent, text=titre,
                 bg=theme.BG, fg=theme.TEXT,
                 font=theme.f_h3(13)).pack(anchor="w")
        tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", pady=(4, 0))
