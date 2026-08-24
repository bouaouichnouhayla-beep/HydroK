import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox

from repositories.point_repository import PointRepository
from repositories.zone_repository import ZoneRepository
from repositories.repetition_repository import RepetitionRepository
from ui.point_dialog import PointDialog
from ui import theme
from ui.error_handler import traiter_erreur_sqlite
from ui.maps import CarteInteractive, PointCarte
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card,
    bouton_primaire, bouton_accent, bouton_secondaire, bouton_danger,
    configurer_zebrage, inserer_ligne, badge,
)


class PointFrame(tk.Frame):

    def __init__(self, parent, controller, zone_id, zone_nom):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller
        self.zone_id = int(zone_id)
        self.zone_nom = zone_nom

        self.point_repo = PointRepository()
        self.repetition_repo = RepetitionRepository()
        self.zone_repo = ZoneRepository()
        self.zone = self.zone_repo.trouver_par_id(self.zone_id)
        self.carte_interactive = None

        self._build()

    def nettoyer(self):
        self.sf.detruire_proprement()

    def refresh(self):
        self.charger_points()

    # ------------------------------------------------------------------
    def _build(self):
        HeaderBar(self, ["HydroK", "Études", self.zone_nom, "Points de mesure"],
                  on_retour=self.controller.show_zones).pack(fill="x")

        self.sf = ScrollableFrame(self, bg=theme.BG)
        self.sf.pack(fill="both", expand=True)

        racine = tk.Frame(self.sf.contenu, bg=theme.BG)
        racine.pack(fill="both", expand=True, padx=36, pady=28)

        # --- Titre + bouton ---
        haut = tk.Frame(racine, bg=theme.BG)
        haut.pack(fill="x", pady=(0, 10))
        tk.Label(haut, text=f"Points de mesure", bg=theme.BG,
                 fg=theme.TEXT, font=theme.f_h1(22)).pack(side="left")
        bouton_primaire(haut, "+ Nouveau point",
                        command=self._ouvrir_creation).pack(side="right", pady=4)

        # --- Bandeau infos zone ---
        self._bandeau_zone(racine)

        # --- Card tableau ---
        card = Card(racine, padding=0)
        card.pack(fill="both", expand=True, pady=(14, 0))

        toolbar = tk.Frame(card.corps, bg=theme.SURFACE)
        toolbar.pack(fill="x", padx=16, pady=14)

        bouton_accent(toolbar, "▶  Saisir répétitions",
                      command=self._ouvrir_repetitions).pack(side="left")
        tk.Frame(toolbar, bg=theme.BORDER, width=1).pack(side="left", fill="y", padx=8)
        bouton_secondaire(toolbar, "✎  Modifier",
                          command=self._modifier).pack(side="left")
        bouton_danger(toolbar, "✕  Supprimer",
                      command=self._supprimer).pack(side="right")

        tk.Frame(card.corps, bg=theme.BORDER, height=1).pack(fill="x")

        # Tableau
        cols = ("nom", "latitude", "longitude", "facies",
                "profondeurs", "nb_rep", "k_moyen")
        self.table = ttk.Treeview(card.corps, columns=cols, show="headings",
                                  selectmode="browse")
        configurer_zebrage(self.table)

        entetes = {
            "nom":         ("Point",              130, "w"),
            "latitude":    ("Coord. N (lat.)",    110, "center"),
            "longitude":   ("Coord. E (lon.)",    110, "center"),
            "facies":      ("Faciès",             120, "center"),
            "profondeurs": ("Profondeurs (cm)",    180, "center"),
            "nb_rep":      ("Rép.",                60, "center"),
            "k_moyen":     ("K moyen (m/s)",      130, "center"),
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

        self.table.bind("<Double-1>", lambda e: self._ouvrir_repetitions())

        self._creer_carte_interactive(racine)
        self.charger_points()

    def _creer_carte_interactive(self, parent):
        """Crée une seule carte sous le tableau de la fenêtre."""
        if self.carte_interactive is not None:
            return
        tk.Label(
            parent,
            text="Localisation des points de mesure",
            bg=theme.BG,
            fg=theme.TEXT,
            font=theme.f_h2(15),
        ).pack(anchor="w", pady=(24, 0))
        self.carte_interactive = CarteInteractive(parent, hauteur=440)
        self.carte_interactive.pack(fill="x", pady=(8, 24))

    # ------------------------------------------------------------------
    def _bandeau_zone(self, parent):
        z = self.zone
        if z is None:
            return

        bg_etat, fg_etat = theme.couleur_statut(z.etat or "en_cours")
        etat_label = {"en_cours": "En cours", "termine": "Terminé"}.get(
            z.etat or "", z.etat or "—")

        bandeau = tk.Frame(parent, bg=theme.SURFACE,
                           highlightbackground=theme.BORDER,
                           highlightthickness=1)
        bandeau.pack(fill="x", pady=(0, 4))

        corps = tk.Frame(bandeau, bg=theme.SURFACE)
        corps.pack(fill="x", padx=16, pady=10)

        tk.Label(corps, text=f"Étude : {z.nom}",
                 bg=theme.SURFACE, fg=theme.TEXT,
                 font=theme.f_body_bold(10)).pack(side="left")

        sep = lambda: tk.Label(corps, text=" · ",
                               bg=theme.SURFACE, fg=theme.BORDER_STRONG,
                               font=theme.f_body(10)).pack(side="left")

        sep()
        tk.Label(corps, text=z.site or "—",
                 bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.f_body(10)).pack(side="left")

        if z.date_campagne:
            sep()
            tk.Label(corps, text=z.date_campagne,
                     bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                     font=theme.f_body(10)).pack(side="left")

        badge(corps, etat_label, bg_etat, fg_etat).pack(
            side="right", padx=(8, 0))

    # ------------------------------------------------------------------
    def charger_points(self):
        for row in self.table.get_children():
            self.table.delete(row)

        points = self.point_repo.lister_par_zone(self.zone_id)
        points_carte = []
        for i, p in enumerate(points):
            nb_rep = self.repetition_repo.compter_par_point(p.id)
            k_moy = self.repetition_repo.moyenne_k_par_point(p.id)
            profondeurs_m = self.repetition_repo.profondeurs_par_point(p.id) or "—"
            profondeurs = theme.format_profondeurs_cm(profondeurs_m)
            k_txt = theme.format_k(k_moy)
            inserer_ligne(self.table, i, str(p.id),
                          (p.nom, p.latitude, p.longitude,
                           p.facies, profondeurs, nb_rep, k_txt))
            points_carte.append(PointCarte(
                nom=p.nom,
                latitude=p.latitude,
                longitude=p.longitude,
                facies=p.facies,
                k_moyen=k_moy,
            ))

        self.carte_interactive.actualiser(points_carte)

    def _selection(self):
        sel = self.table.selection()
        if not sel:
            return None, None
        return int(sel[0]), self.table.item(sel[0])["values"][0]

    # ------------------------------------------------------------------
    def _ouvrir_creation(self):
        PointDialog(parent=self, zone_id=self.zone_id,
                    refresh_callback=self.charger_points)

    def _modifier(self):
        pid, _ = self._selection()
        if pid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord un point.")
            return
        point = self.point_repo.trouver_par_id(pid)
        if point:
            PointDialog(parent=self, zone_id=self.zone_id,
                        refresh_callback=self.charger_points, point=point)

    def _supprimer(self):
        pid, nom = self._selection()
        if pid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord un point.")
            return
        if messagebox.askyesno("Supprimer", f"Supprimer le point « {nom} » et toutes ses répétitions ?"):
            try:
                self.point_repo.supprimer(pid)
            except (sqlite3.IntegrityError, sqlite3.OperationalError,
                    sqlite3.DatabaseError) as erreur:
                traiter_erreur_sqlite(erreur, self, "la suppression du point")
                return
            self.charger_points()

    def _ouvrir_repetitions(self):
        pid, nom = self._selection()
        if pid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord un point.")
            return
        self.controller.show_repetitions(pid, str(nom))
