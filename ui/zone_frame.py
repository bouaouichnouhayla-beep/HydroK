import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox

from repositories.zone_repository import ZoneRepository
from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository
from services.export_csv_service import ExportCsvService
from services.export_pdf_service import ExportPdfService
from ui.export_dialog import ExportDialog
from ui.export_pdf_dialog import ExportPdfDialog
from ui.zone_dialog import ZoneDialog
from ui import theme
from ui.error_handler import traiter_erreur_sqlite
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card,
    bouton_primaire, bouton_accent, bouton_secondaire, bouton_danger,
    configurer_zebrage, inserer_ligne,
)


class ZoneFrame(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller
        self.zone_repo = ZoneRepository()
        self.point_repo = PointRepository()
        self.repetition_repo = RepetitionRepository()
        self.export_csv_service = ExportCsvService()
        self.export_pdf_service = ExportPdfService()
        self._build()

    # ------------------------------------------------------------------
    def nettoyer(self):
        self.sf.detruire_proprement()

    def refresh(self):
        self.charger_zones()

    # ------------------------------------------------------------------
    def _build(self):
        HeaderBar(self, ["HydroK", "Études"],
                  on_retour=self.controller.show_home).pack(fill="x")

        self.sf = ScrollableFrame(self, bg=theme.BG)
        self.sf.pack(fill="both", expand=True)

        racine = tk.Frame(self.sf.contenu, bg=theme.BG)
        racine.pack(fill="both", expand=True, padx=36, pady=28)

        # Titre + bouton ajout
        haut = tk.Frame(racine, bg=theme.BG)
        haut.pack(fill="x", pady=(0, 16))

        tk.Label(haut, text="Études", bg=theme.BG,
                 fg=theme.TEXT, font=theme.f_h1(22)).pack(side="left")

        bouton_primaire(haut, "+ Nouvelle étude",
                        command=self._ouvrir_creation).pack(side="right", pady=4)

        # Card principale
        card = Card(racine, padding=0)
        card.pack(fill="both", expand=True)


        toolbar = tk.Frame(card.corps, bg=theme.SURFACE)
        toolbar.pack(fill="x", padx=16, pady=(14, 8))

        bouton_accent(toolbar, "▶  Ouvrir",
                    command=self._ouvrir_zone).pack(side="left", padx=(0, 8), pady=3)

        bouton_secondaire(toolbar, "📊  Synthèse",
                        command=self._ouvrir_synthese).pack(side="left", padx=(0, 8), pady=3)

        bouton_secondaire(toolbar, "Exporter les données",
                        command=self._exporter_donnees).pack(side="left", padx=(0, 8), pady=3)

        bouton_secondaire(toolbar, "Exporter PDF",
                        command=self._exporter_pdf).pack(side="left", padx=(0, 8), pady=3)

        bouton_secondaire(toolbar, "✎  Modifier",
                        command=self._modifier_zone).pack(side="left", padx=(0, 8), pady=3)

        bouton_danger(toolbar, "✕  Supprimer",
                    command=self._supprimer_zone).pack(side="left", padx=(0, 8), pady=3)

        tk.Frame(card.corps, bg=theme.BORDER, height=1).pack(fill="x")


        # Tableau
        cols = ("id", "nom", "site", "date", "operateur", "points", "repetitions", "etat")
        self.table = ttk.Treeview(card.corps, columns=cols, show="headings",
                                  selectmode="browse")
        configurer_zebrage(self.table)

        entetes = {
            "id": ("#", 44, "center"),
            "nom": ("Nom de l'étude", 210, "w"),
            "site": ("Cours d'eau / Site", 200, "w"),
            "date": ("Date", 100, "center"),
            "operateur": ("Opérateur", 130, "center"),
            "points": ("Points", 70, "center"),
            "repetitions": ("Rép.", 70, "center"),
            "etat": ("État", 110, "center"),
        }
        for col, (label, larg, anch) in entetes.items():
            self.table.heading(col, text=label)
            self.table.column(col, width=larg, anchor=anch, minwidth=40)

        vsb = ttk.Scrollbar(card.corps, orient="vertical",
                            command=self.table.yview)
        self.table.configure(yscrollcommand=vsb.set)

        self.table.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=16)
        vsb.pack(side="right", fill="y", pady=16, padx=(0, 6))

        # Double-clic pour ouvrir directement
        self.table.bind("<Double-1>", lambda e: self._ouvrir_zone())

        
        self.charger_zones()

    # ------------------------------------------------------------------
    def charger_zones(self):
        for row in self.table.get_children():
            self.table.delete(row)

        zones = self.zone_repo.lister()
        for i, z in enumerate(zones):
            points_zone = self.point_repo.lister_par_zone(z.id)
            nb_pts = len(points_zone)

            nb_rep = 0
            for p in points_zone:
                nb_rep += len(self.repetition_repo.lister_par_point(p.id))

            etat_label = {"en_cours": "En cours", "termine": "Terminé"}.get(
                z.etat or "", z.etat or "—")
            inserer_ligne(self.table, i, str(z.id),
                          (i + 1, z.nom, z.site, z.date_campagne,
                           z.operateur, nb_pts, nb_rep, etat_label))

    def _selection(self):
        sel = self.table.selection()
        if not sel:
            return None

        # L'identifiant réel de la zone est stocké dans l'iid du Treeview
        # grâce à inserer_ligne(..., iid=str(z.id), ...).
        # La colonne # affiche seulement une numérotation visuelle (1, 2, 3...).
        zone_id = int(sel[0])
        vals = self.table.item(sel[0])["values"]

        return zone_id, vals

    # ------------------------------------------------------------------
    def _ouvrir_creation(self):
        ZoneDialog(parent=self, refresh_callback=self.charger_zones)

    def _modifier_zone(self):
        selection = self._selection()
        if not selection:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une étude.")
            return

        zone_id, vals = selection
        zone = self.zone_repo.trouver_par_id(zone_id)

        if zone:
            ZoneDialog(parent=self, refresh_callback=self.charger_zones, zone=zone)
            self.controller.invalidate_points_cache(zone_id)

    def _supprimer_zone(self):
        selection = self._selection()
        if not selection:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une étude.")
            return

        zone_id, vals = selection
        nom = vals[1]

        if messagebox.askyesno("Supprimer", f"Supprimer l'étude « {nom} » et toutes ses données ?"):
            try:
                self.zone_repo.supprimer(zone_id)
            except (sqlite3.IntegrityError, sqlite3.OperationalError,
                    sqlite3.DatabaseError) as erreur:
                traiter_erreur_sqlite(erreur, self, "la suppression de l'étude")
                return
            self.controller.invalidate_points_cache(zone_id)
            self.charger_zones()

    def _ouvrir_zone(self):
        selection = self._selection()
        if not selection:
            return

        zone_id, vals = selection
        self.controller.show_points(zone_id, str(vals[1]))

    def _ouvrir_synthese(self):
        selection = self._selection()
        if not selection:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une étude.")
            return

        zone_id, vals = selection
        self.controller.show_zone_synthese(zone_id, str(vals[1]))

    def _exporter_donnees(self):
        """Ouvre la préparation de l'export pour la zone choisie."""
        selection = self._selection()
        if not selection:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une étude.")
            return

        zone_id, valeurs = selection
        ExportDialog(
            parent=self,
            zone_id=zone_id,
            nom_etude=str(valeurs[1]),
            export_csv_service=self.export_csv_service,
        )

    def _exporter_pdf(self):
        """Ouvre la préparation du rapport PDF pour la zone choisie."""
        selection = self._selection()
        if not selection:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une étude.")
            return

        zone_id, valeurs = selection
        ExportPdfDialog(
            parent=self,
            zone_id=zone_id,
            nom_etude=str(valeurs[1]),
            export_pdf_service=self.export_pdf_service,
        )
