"""Dialogue HydroK de préparation de l'export PDF."""

from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from ui import theme
from ui.widgets import (
    Card, HeaderBar, bouton_accent, bouton_secondaire,
    champ_entry, champ_libelle, separateur,
)
from ui.error_handler import afficher_erreur_export
from utils.logging_config import obtenir_logger


logger = obtenir_logger(__name__)


class ExportPdfDialog:
    """Présente le rapport attendu avant de choisir sa destination."""

    def __init__(self, parent, zone_id, nom_etude, export_pdf_service):
        self.zone_id = int(zone_id)
        self.nom_etude = str(nom_etude)
        self.export_pdf_service = export_pdf_service
        self.instant = datetime.now()

        self.window = tk.Toplevel(parent)
        self.window.title("HydroK — Exporter PDF")
        self.window.geometry("680x460")
        self.window.configure(bg=theme.BG)
        self.window.grab_set()
        self.window.resizable(False, False)
        self.window.transient(parent.winfo_toplevel())
        self.dossier = tk.StringVar(master=self.window)
        self.nom_fichier = self._nom_fichier_prevu()

        HeaderBar(
            self.window,
            ["HydroK", "Études", self.nom_etude, "Exporter PDF"],
        ).pack(fill="x")

        contenu = tk.Frame(self.window, bg=theme.BG)
        contenu.pack(fill="both", expand=True, padx=30, pady=24)
        tk.Label(
            contenu, text="Exporter PDF", bg=theme.BG,
            fg=theme.TEXT, font=theme.f_h1(20),
        ).pack(anchor="w")
        tk.Label(
            contenu,
            text="Un rapport A4 imprimable sera généré pour cette étude.",
            bg=theme.BG, fg=theme.TEXT_MUTED, font=theme.f_body(10),
        ).pack(anchor="w", pady=(4, 16))

        card = Card(contenu, titre="Fichier à créer", padding=18)
        card.pack(fill="x")
        tk.Label(
            card.corps, text=f"✓  {self.nom_fichier}",
            bg=theme.SURFACE, fg=theme.TEXT,
            font=theme.f_body(10), anchor="w",
        ).pack(fill="x", pady=3)

        ligne_dossier = tk.Frame(contenu, bg=theme.BG)
        ligne_dossier.pack(fill="x", pady=(18, 0))
        champ_libelle(
            ligne_dossier, "Dossier de destination", bg=theme.BG
        ).pack(anchor="w")
        choix_dossier = tk.Frame(ligne_dossier, bg=theme.BG)
        choix_dossier.pack(fill="x", pady=(5, 0))
        champ_entry(
            choix_dossier, textvariable=self.dossier, state="readonly",
            readonlybackground=theme.SURFACE,
        ).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        bouton_secondaire(
            choix_dossier, "Parcourir...", command=self._parcourir
        ).pack(side="right")

        separateur(contenu, bg=theme.BORDER).pack(fill="x", pady=20)
        barre = tk.Frame(contenu, bg=theme.BG)
        barre.pack(fill="x")
        bouton_secondaire(
            barre, "Annuler", command=self.window.destroy
        ).pack(side="left")
        self.bouton_exporter = bouton_accent(
            barre, "Exporter", command=self._exporter, state="disabled"
        )
        self.bouton_exporter.pack(side="right")

    def _nom_fichier_prevu(self):
        horodatage = self.instant.strftime("%Y-%m-%d_%H-%M")
        nom = self.export_pdf_service._nom_fichier(self.nom_etude)
        return f"{nom}_rapport_{horodatage}.pdf"

    def _parcourir(self):
        dossier = filedialog.askdirectory(
            parent=self.window, title="Choisir le dossier d'export",
            mustexist=True,
        )
        if dossier:
            self.dossier.set(dossier)
            self._actualiser_bouton()

    def _actualiser_bouton(self):
        self.bouton_exporter.configure(
            state="normal" if Path(self.dossier.get()).is_dir() else "disabled"
        )

    def _exporter(self):
        dossier = self.dossier.get()
        if not Path(dossier).is_dir():
            self._actualiser_bouton()
            return
        try:
            chemin = self.export_pdf_service.exporter_zone(
                self.zone_id, self.nom_etude, dossier, instant=self.instant
            )
        except FileExistsError:
            if not messagebox.askyesno(
                "HydroK", "Ce rapport existe déjà. Voulez-vous le remplacer ?",
                parent=self.window,
            ):
                return
            try:
                chemin = self.export_pdf_service.exporter_zone(
                    self.zone_id, self.nom_etude, dossier,
                    ecraser=True, instant=self.instant,
                )
            except OSError as erreur:
                self._afficher_erreur(erreur)
                return
        except OSError as erreur:
            self._afficher_erreur(erreur)
            return

        messagebox.showinfo(
            "HydroK",
            "Export PDF terminé avec succès.\n\n"
            f"✓ {chemin.name}",
            parent=self.window,
        )
        self.window.destroy()

    def _afficher_erreur(self, erreur):
        logger.exception("Échec de l'export PDF")
        raison = "permission" if isinstance(erreur, PermissionError) else "dossier"
        afficher_erreur_export(self.window, raison)
