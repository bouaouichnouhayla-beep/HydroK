"""
ui/sonde_dialog.py
=================================================
IMPORTANT — unités : les champs sont saisis en CENTIMÈTRES (cm),
plus pratiques pour décrire le matériel. Ils sont convertis en
mètres avant stockage en base (cohérent avec les répétitions et
avec les formules de services/CalculerK.py, qui travaillent en
mètres).
=================================================
"""
import tkinter as tk
import sqlite3
from tkinter import messagebox
from ui.error_handler import traiter_erreur_sqlite
from pathlib import Path

from models import Sonde
from repositories.sonde_repository import SondeRepository
from ui import theme
from ui.schema_image import SchemaImage
from ui.widgets import (
    HeaderBar, Card, ScrollableFrame,
    bouton_accent, bouton_secondaire,
    champ_libelle, champ_entry, separateur,
)

CM_VERS_M = 0.01
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = BASE_DIR / "assets" / "schemas"


class SondeDialog:

    def __init__(self, parent, refresh_callback=None, sonde=None):
        self.sonde = sonde
        self.refresh_callback = refresh_callback
        self.repo = SondeRepository()
        self.photo_image = None

        est_modif = sonde is not None
        titre = "Modifier la sonde" if est_modif else "Nouvelle sonde"

        self.window = tk.Toplevel(parent)
        self.window.title(f"HydroK — {titre}")
        self.window.geometry("760x560")
        self.window.configure(bg=theme.BG)
        self.window.grab_set()
        self.window.resizable(True, True)
        self.window.minsize(680, 480)

        HeaderBar(self.window, ["HydroK", "Matériel", titre]).pack(fill="x")

        sf = ScrollableFrame(self.window, bg=theme.BG)
        sf.pack(fill="both", expand=True)
        contenu = tk.Frame(sf.contenu, bg=theme.BG)
        contenu.pack(fill="both", expand=True, padx=28, pady=22)

        tk.Label(contenu, text=titre, bg=theme.BG,
                 fg=theme.TEXT, font=theme.f_h1(20)).pack(anchor="w", pady=(0, 4))
        tk.Label(contenu, text="Toutes les longueurs sont saisies en CENTIMÈTRES (cm).",
                 bg=theme.BG, fg=theme.TEXT_MUTED,
                 font=theme.f_small(9)).pack(anchor="w", pady=(0, 16))

        zone = tk.Frame(contenu, bg=theme.BG)
        zone.pack(fill="both", expand=True)

        gauche = tk.Frame(zone, bg=theme.BG)
        gauche.pack(side="left", fill="both", expand=True, padx=(0, 14))

        droite = tk.Frame(zone, bg=theme.BG, width=260)
        droite.pack(side="right", fill="y")
        droite.pack_propagate(False)

        card = Card(gauche, titre="Caractéristiques de la sonde", padding=18)
        card.pack(fill="x")

        champ_libelle(card.corps, "Nom de la sonde", obligatoire=True).pack(anchor="w")
        self.entry_nom = champ_entry(card.corps)
        self.entry_nom.pack(fill="x", ipady=5, pady=(4, 12))

        champ_libelle(card.corps, "Longueur totale (cm)", obligatoire=True).pack(anchor="w")
        self.entry_long_totale = champ_entry(card.corps)
        self.entry_long_totale.pack(fill="x", ipady=5, pady=(4, 12))

        row = tk.Frame(card.corps, bg=theme.SURFACE)
        row.pack(fill="x", pady=(0, 12))
        col_d = tk.Frame(row, bg=theme.SURFACE)
        col_d.pack(side="left", fill="x", expand=True, padx=(0, 8))
        champ_libelle(col_d, "Diamètre intérieur (cm)", obligatoire=True).pack(anchor="w")
        self.entry_diam = champ_entry(col_d)
        self.entry_diam.pack(fill="x", ipady=5, pady=(4, 0))

        col_l = tk.Frame(row, bg=theme.SURFACE)
        col_l.pack(side="left", fill="x", expand=True)
        champ_libelle(col_l, "Longueur crépine (cm)", obligatoire=True).pack(anchor="w")
        self.entry_long = champ_entry(col_l)
        self.entry_long.pack(fill="x", ipady=5, pady=(4, 0))

        card_photo = Card(droite, titre="Sonde sélectionnée", padding=14)
        card_photo.pack(fill="both", expand=True)
        self.canvas_photo = tk.Canvas(
            card_photo.corps,
            width=230,
            height=330,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self.canvas_photo.pack(fill="both", expand=True)
        self.schema_sonde = SchemaImage(self.canvas_photo)
        self._afficher_photo_sonde()

        if est_modif:
            self.entry_nom.insert(0, sonde.nom or "")
            if getattr(sonde, "longueur_totale", None) is not None:
                self.entry_long_totale.insert(0, f"{sonde.longueur_totale / CM_VERS_M:g}")
            if sonde.diametre_interieur is not None:
                self.entry_diam.insert(0, f"{sonde.diametre_interieur / CM_VERS_M:g}")
            if sonde.longueur_crepine is not None:
                self.entry_long.insert(0, f"{sonde.longueur_crepine / CM_VERS_M:g}")

        separateur(contenu, height=1, bg=theme.BORDER).pack(fill="x", pady=18)
        barre = tk.Frame(contenu, bg=theme.BG)
        barre.pack(fill="x")
        bouton_secondaire(barre, "Annuler", command=self.window.destroy).pack(side="left")
        texte_btn = "Enregistrer les modifications" if est_modif else "Créer la sonde"
        bouton_accent(barre, texte_btn, command=self._enregistrer).pack(side="right")

    def _afficher_photo_sonde(self):
        self.schema_sonde.afficher(
            SCHEMAS_DIR / "sonde.png", "Sonde piézométrique"
        )

    def _lire_cm(self, entry):
        val = entry.get().strip()
        return float(val) * CM_VERS_M if val else None

    def _enregistrer(self):
        nom = self.entry_nom.get().strip()

        if not nom:
            messagebox.showerror("Champ obligatoire", "Le nom est obligatoire.",
                                 parent=self.window)
            return
        try:
            long_totale_m = self._lire_cm(self.entry_long_totale)
            diam_m = self._lire_cm(self.entry_diam)
            long_crepine_m = self._lire_cm(self.entry_long)
        except ValueError:
            messagebox.showerror("Valeur invalide",
                                 "Les longueurs et le diamètre doivent être des nombres.",
                                 parent=self.window)
            return

        if not diam_m or not long_crepine_m:
            messagebox.showerror("Champ obligatoire",
                                 "Le diamètre intérieur et la longueur de crépine "
                                 "sont obligatoires.", parent=self.window)
            return

        sonde = Sonde(
            nom=nom,
            longueur_totale=long_totale_m if long_totale_m is not None else 0.0,
            diametre_interieur=diam_m,
            longueur_crepine=long_crepine_m,
        )
        try:
            if self.sonde:
                sonde.id = self.sonde.id
                self.repo.modifier(sonde)
            else:
                self.repo.ajouter(sonde)
        except (sqlite3.IntegrityError, sqlite3.OperationalError,
                sqlite3.DatabaseError) as erreur:
            traiter_erreur_sqlite(erreur, self.window, "l'enregistrement de la sonde")
            return

        if self.refresh_callback:
            self.refresh_callback()
        self.window.destroy()
