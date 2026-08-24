"""
ui/outil_dialog.py
=================================================
IMPORTANT — unités : tous les champs de dimensions sont saisis
en CENTIMÈTRES (cm) et convertis en mètres avant stockage, pour
rester cohérents avec le reste de la base et avec les formules
de services/CalculerK.py (qui travaillent en mètres).
=================================================
"""
import tkinter as tk
import sqlite3
from tkinter import messagebox
from ui.error_handler import traiter_erreur_sqlite
from pathlib import Path

from models import Entonnoir, Tuyau
from repositories.outil_repository import OutilRepository
from ui import theme
from ui.schema_image import SchemaImage
from ui.widgets import (
    HeaderBar, Card, ScrollableFrame,
    bouton_accent, bouton_secondaire,
    champ_libelle, champ_entry, champ_combobox, separateur,
)

CM_VERS_M = 0.01
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = BASE_DIR / "assets" / "schemas"


class OutilDialog:

    def __init__(self, parent, refresh_callback=None, outil=None):
        self.outil = outil
        self.refresh_callback = refresh_callback
        self.repo = OutilRepository()
        self.photo_image = None

        est_modif = outil is not None
        titre = "Modifier l'outil" if est_modif else "Nouvel outil"

        self.window = tk.Toplevel(parent)
        self.window.title(f"HydroK — {titre}")
        self.window.geometry("820x660")
        self.window.configure(bg=theme.BG)
        self.window.grab_set()
        self.window.resizable(True, True)
        self.window.minsize(720, 560)

        HeaderBar(self.window, ["HydroK", "Matériel", titre]).pack(fill="x")

        sf = ScrollableFrame(self.window, bg=theme.BG)
        sf.pack(fill="both", expand=True)
        contenu = tk.Frame(sf.contenu, bg=theme.BG)
        contenu.pack(fill="both", expand=True, padx=28, pady=22)

        tk.Label(contenu, text=titre, bg=theme.BG,
                 fg=theme.TEXT, font=theme.f_h1(20)).pack(anchor="w", pady=(0, 4))
        tk.Label(contenu, text="Toutes les dimensions sont saisies en CENTIMÈTRES (cm).",
                 bg=theme.BG, fg=theme.TEXT_MUTED,
                 font=theme.f_small(9)).pack(anchor="w", pady=(0, 16))

        zone = tk.Frame(contenu, bg=theme.BG)
        zone.pack(fill="both", expand=True)

        gauche = tk.Frame(zone, bg=theme.BG)
        gauche.pack(side="left", fill="both", expand=True, padx=(0, 14))

        droite = tk.Frame(zone, bg=theme.BG, width=260)
        droite.pack(side="right", fill="y")
        droite.pack_propagate(False)

        card = Card(gauche, titre="Caractéristiques de l'outil", padding=18)
        card.pack(fill="x")

        champ_libelle(card.corps, "Nom de l'outil", obligatoire=True).pack(anchor="w")
        self.entry_nom = champ_entry(card.corps)
        self.entry_nom.pack(fill="x", ipady=5, pady=(4, 12))

        champ_libelle(card.corps, "Type d'outil", obligatoire=True).pack(anchor="w")
        self.combo_type = champ_combobox(card.corps,
                                         values=["entonnoir", "tuyau"],
                                         state="readonly")
        self.combo_type.pack(fill="x", ipady=4, pady=(4, 12))
        self.combo_type.bind("<<ComboboxSelected>>", self._on_type_change)

        # Bloc TUYAU
        self.bloc_tuyau = tk.Frame(card.corps, bg=theme.SURFACE)
        grille_t = tk.Frame(self.bloc_tuyau, bg=theme.SURFACE)
        grille_t.pack(fill="x")
        grille_t.columnconfigure(0, weight=1)
        grille_t.columnconfigure(1, weight=1)

        bloc_dt = tk.Frame(grille_t, bg=theme.SURFACE)
        bloc_dt.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))
        champ_libelle(bloc_dt, "Diamètre tuyau (cm)").pack(anchor="w")
        self.entry_diam_tuyau = champ_entry(bloc_dt)
        self.entry_diam_tuyau.pack(fill="x", ipady=5, pady=(4, 0))

        bloc_ht = tk.Frame(grille_t, bg=theme.SURFACE)
        bloc_ht.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 10))
        champ_libelle(bloc_ht, "Hauteur tuyau (cm)").pack(anchor="w")
        self.entry_haut_tuyau = champ_entry(bloc_ht)
        self.entry_haut_tuyau.pack(fill="x", ipady=5, pady=(4, 0))

        # Bloc ENTONNOIR
        self.bloc_entonnoir = tk.Frame(card.corps, bg=theme.SURFACE)
        grille_e = tk.Frame(self.bloc_entonnoir, bg=theme.SURFACE)
        grille_e.pack(fill="x")
        grille_e.columnconfigure(0, weight=1)
        grille_e.columnconfigure(1, weight=1)

        params_entonnoir = [
            ("L1", "L1 (cm)"), ("L2", "L2 (cm)"),
            ("D1", "D1 (cm)"), ("D2", "D2 (cm)"), ("D3", "D3 (cm)"),
        ]
        self.entries_entonnoir = {}
        for idx, (cle, label) in enumerate(params_entonnoir):
            col = idx % 2
            row = idx // 2
            bloc = tk.Frame(grille_e, bg=theme.SURFACE)
            bloc.grid(row=row, column=col, sticky="ew",
                      padx=(0, 8) if col == 0 else (8, 0), pady=(0, 10))
            champ_libelle(bloc, label).pack(anchor="w")
            e = champ_entry(bloc)
            e.pack(fill="x", ipady=5, pady=(4, 0))
            self.entries_entonnoir[cle] = e

        card_photo = Card(droite, titre="Outil sélectionné", padding=14)
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
        self.schema_outil = SchemaImage(self.canvas_photo)

        # Affichage initial selon le type
        if est_modif:
            self.combo_type.set(outil.type_outil or "")
        self._on_type_change()

        if est_modif:
            self.entry_nom.insert(0, outil.nom or "")
            if outil.type_outil == "tuyau":
                if getattr(outil, "diametre_interieur", None) is not None:
                    self.entry_diam_tuyau.insert(0, f"{outil.diametre_interieur / CM_VERS_M:g}")
                if getattr(outil, "hauteur_tuyau", None) is not None:
                    self.entry_haut_tuyau.insert(0, f"{outil.hauteur_tuyau / CM_VERS_M:g}")
            else:
                for cle in ("L1", "L2", "D1", "D2", "D3"):
                    val = getattr(outil, cle, None)
                    if val is not None:
                        self.entries_entonnoir[cle].insert(0, f"{val / CM_VERS_M:g}")

        separateur(contenu, height=1, bg=theme.BORDER).pack(fill="x", pady=18)
        barre = tk.Frame(contenu, bg=theme.BG)
        barre.pack(fill="x")
        bouton_secondaire(barre, "Annuler", command=self.window.destroy).pack(side="left")
        texte_btn = "Enregistrer les modifications" if est_modif else "Créer l'outil"
        bouton_accent(barre, texte_btn, command=self._enregistrer).pack(side="right")

    # ------------------------------------------------------------------
    def _on_type_change(self, event=None):
        type_outil = self.combo_type.get()
        self.bloc_tuyau.pack_forget()
        self.bloc_entonnoir.pack_forget()

        if type_outil == "tuyau":
            self.bloc_tuyau.pack(fill="x", pady=(0, 8))
        elif type_outil == "entonnoir":
            self.bloc_entonnoir.pack(fill="x", pady=(0, 8))

        self._afficher_photo_outil(type_outil)

    def _afficher_photo_outil(self, type_outil):
        if type_outil == "tuyau":
            nom_fichier = "tuyau.png"
            titre = "Tuyau"
        elif type_outil == "entonnoir":
            nom_fichier = "entonnoir.png"
            titre = "Entonnoir"
        else:
            self.schema_outil.afficher_message(
                "Choisissez un type d'outil\npour afficher le schéma."
            )
            return
        self.schema_outil.afficher(SCHEMAS_DIR / nom_fichier, titre)

    def _lire_cm(self, entry):
        val = entry.get().strip()
        return float(val) * CM_VERS_M if val else None

    def _enregistrer(self):
        nom = self.entry_nom.get().strip()
        type_outil = self.combo_type.get().strip()

        if not nom:
            messagebox.showerror("Champ obligatoire", "Le nom est obligatoire.",
                                 parent=self.window)
            return
        if type_outil not in ("entonnoir", "tuyau"):
            messagebox.showerror("Champ obligatoire", "Le type d'outil est obligatoire.",
                                 parent=self.window)
            return

        try:
            if type_outil == "tuyau":
                outil = Tuyau(
                    nom=nom,
                    type_outil="tuyau",
                    diametre_interieur=self._lire_cm(self.entry_diam_tuyau) or 0.0,
                    hauteur_tuyau=self._lire_cm(self.entry_haut_tuyau) or 0.0,
                )
            else:
                outil = Entonnoir(
                    nom=nom,
                    type_outil="entonnoir",
                    L1=self._lire_cm(self.entries_entonnoir["L1"]) or 0.0,
                    L2=self._lire_cm(self.entries_entonnoir["L2"]) or 0.0,
                    D1=self._lire_cm(self.entries_entonnoir["D1"]) or 0.0,
                    D2=self._lire_cm(self.entries_entonnoir["D2"]) or 0.0,
                    D3=self._lire_cm(self.entries_entonnoir["D3"]) or 0.0,
                )
        except ValueError:
            messagebox.showerror("Valeur invalide",
                                 "Toutes les dimensions doivent être des nombres.",
                                 parent=self.window)
            return

        try:
            if self.outil:
                outil.id = self.outil.id
                if type_outil == "tuyau":
                    self.repo.modifier_tuyau(outil)
                else:
                    self.repo.modifier_entonnoir(outil)
            else:
                if type_outil == "tuyau":
                    self.repo.ajouter_tuyau(outil)
                else:
                    self.repo.ajouter_entonnoir(outil)
        except (sqlite3.IntegrityError, sqlite3.OperationalError,
                sqlite3.DatabaseError) as erreur:
            traiter_erreur_sqlite(erreur, self.window, "l'enregistrement de l'outil")
            return

        if self.refresh_callback:
            self.refresh_callback()
        self.window.destroy()
