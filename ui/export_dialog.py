"""Dialogue HydroK de préparation de l'export des données."""

from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from ui import theme
from ui.widgets import (
    Card,
    HeaderBar,
    bouton_accent,
    bouton_secondaire,
    champ_entry,
    champ_libelle,
    separateur,
)
from ui.error_handler import afficher_erreur_export
from utils.logging_config import obtenir_logger


logger = obtenir_logger(__name__)


class ExportDialog:
    """Présente les fichiers attendus avant de choisir leur destination."""

    def __init__(self, parent, zone_id, nom_etude, export_csv_service):
        self.zone_id = int(zone_id)
        self.nom_etude = str(nom_etude)
        self.export_csv_service = export_csv_service
        self.instant = datetime.now()

        self.window = tk.Toplevel(parent)
        self.window.title("HydroK — Exporter les données")
        self.window.geometry("680x500")
        self.window.configure(bg=theme.BG)
        self.window.grab_set()
        self.window.resizable(False, False)
        self.window.transient(parent.winfo_toplevel())
        self.dossier = tk.StringVar(master=self.window)
        self.noms_fichiers = self._noms_fichiers_prevus()

        HeaderBar(
            self.window,
            ["HydroK", "Études", self.nom_etude, "Exporter les données"],
        ).pack(fill="x")

        contenu = tk.Frame(self.window, bg=theme.BG)
        contenu.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(
            contenu, text="Exporter les données",
            bg=theme.BG, fg=theme.TEXT, font=theme.f_h1(20),
        ).pack(anchor="w")
        tk.Label(
            contenu,
            text=(
                "Deux fichiers CSV seront générés : les points et "
                "répétitions, puis le matériel utilisé."
            ),
            bg=theme.BG, fg=theme.TEXT_MUTED, font=theme.f_body(10),
            justify="left",
        ).pack(anchor="w", pady=(4, 16))

        card = Card(contenu, titre="Fichiers à créer", padding=18)
        card.pack(fill="x")
        for nom_fichier in self.noms_fichiers:
            tk.Label(
                card.corps, text=f"✓  {nom_fichier}",
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
        self.entry_dossier = champ_entry(
            choix_dossier,
            textvariable=self.dossier,
            state="readonly",
            readonlybackground=theme.SURFACE,
        )
        self.entry_dossier.pack(
            side="left", fill="x", expand=True, ipady=6, padx=(0, 8)
        )
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

    def _noms_fichiers_prevus(self):
        """Construit l'aperçu avec le même nom et le même instant que l'export."""
        horodatage = self.instant.strftime("%Y-%m-%d_%H-%M")
        nom = self.export_csv_service._nom_fichier(self.nom_etude)
        return (
            f"{nom}_repetitions_{horodatage}.csv",
            f"{nom}_materiel_{horodatage}.csv",
        )

    def _parcourir(self):
        """Ouvre le sélecteur système et mémorise un dossier valide."""
        dossier = filedialog.askdirectory(
            parent=self.window,
            title="Choisir le dossier d'export",
            mustexist=True,
        )
        if not dossier:
            return

        self.dossier.set(dossier)
        self._actualiser_bouton_exporter()

    def _actualiser_bouton_exporter(self):
        est_valide = Path(self.dossier.get()).is_dir()
        self.bouton_exporter.configure(
            state="normal" if est_valide else "disabled"
        )

    def _exporter(self):
        """Délègue les deux écritures au service CSV existant."""
        dossier = self.dossier.get()
        if not Path(dossier).is_dir():
            self._actualiser_bouton_exporter()
            messagebox.showerror(
                "HydroK", "Sélectionnez un dossier de destination valide.",
                parent=self.window,
            )
            return

        try:
            chemins = self.export_csv_service.exporter_zone(
                self.zone_id, self.nom_etude, dossier, instant=self.instant
            )
        except FileExistsError:
            if not messagebox.askyesno(
                "HydroK",
                "Les fichiers de cet export existent déjà. "
                "Voulez-vous les remplacer ?",
                parent=self.window,
            ):
                return
            try:
                chemins = self.export_csv_service.exporter_zone(
                    self.zone_id, self.nom_etude, dossier,
                    ecraser=True, instant=self.instant,
                )
            except (PermissionError, OSError) as erreur:
                self._afficher_erreur(erreur)
                return
        except (PermissionError, OSError) as erreur:
            self._afficher_erreur(erreur)
            return

        messagebox.showinfo(
            "HydroK",
            "Export terminé avec succès.\n\n"
            "Les fichiers suivants ont été créés :\n\n"
            f"✓ {chemins[0].name}\n\n"
            f"✓ {chemins[1].name}",
            parent=self.window,
        )
        self.window.destroy()

    def _afficher_erreur(self, erreur):
        logger.exception("Échec de l'export CSV")
        raison = "permission" if isinstance(erreur, PermissionError) else "dossier"
        afficher_erreur_export(self.window, raison)
