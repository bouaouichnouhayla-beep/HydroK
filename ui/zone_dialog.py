import tkinter as tk
import sqlite3
from tkinter import messagebox
from ui.error_handler import traiter_erreur_sqlite
from datetime import date

from models import Zone
from repositories.zone_repository import ZoneRepository
from ui import theme
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card,
    bouton_accent, bouton_secondaire,
    champ_libelle, champ_entry, champ_texte, champ_combobox, separateur,
)


class ZoneDialog:

    def __init__(self, parent, refresh_callback=None, zone=None):
        self.refresh_callback = refresh_callback
        self.zone = zone
        self.repo = ZoneRepository()

        est_modif = zone is not None
        titre_page = "Modifier l'étude" if est_modif else "Nouvelle étude"

        self.window = tk.Toplevel(parent)
        self.window.title(f"HydroK — {titre_page}")
        self.window.geometry("680x620")
        self.window.configure(bg=theme.BG)
        self.window.grab_set()
        self.window.resizable(True, True)
        self.window.minsize(560, 500)

        # --- Header ---
        HeaderBar(self.window,
                  ["HydroK", "Études", titre_page]).pack(fill="x")

        # --- Zone scrollable ---
        sf = ScrollableFrame(self.window, bg=theme.BG)
        sf.pack(fill="both", expand=True)

        contenu = tk.Frame(sf.contenu, bg=theme.BG)
        contenu.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(contenu, text=titre_page,
                 bg=theme.BG, fg=theme.TEXT,
                 font=theme.f_h1(20)).pack(anchor="w")
        tk.Label(contenu,
                 text="Les champs marqués * sont obligatoires.",
                 bg=theme.BG, fg=theme.TEXT_MUTED,
                 font=theme.f_small(9)).pack(anchor="w", pady=(4, 16))

        # --- Card formulaire ---
        card = Card(contenu, titre="Informations générales", padding=20)
        card.pack(fill="x")

        self._champ(card.corps, "Nom de l'étude", obligatoire=True,
                    attr="entry_nom")
        self._champ(card.corps, "Cours d'eau / Site", obligatoire=True,
                    attr="entry_site")

        # Date + opérateur côte à côte
        row2 = tk.Frame(card.corps, bg=theme.SURFACE)
        row2.pack(fill="x", pady=(0, 12))

        col_date = tk.Frame(row2, bg=theme.SURFACE)
        col_date.pack(side="left", fill="x", expand=True, padx=(0, 8))
        champ_libelle(col_date, "Date de campagne", obligatoire=True).pack(anchor="w")
        self.entry_date = champ_entry(col_date)
        self.entry_date.insert(0, str(date.today()))
        self.entry_date.pack(fill="x", ipady=5, pady=(4, 0))

        col_op = tk.Frame(row2, bg=theme.SURFACE)
        col_op.pack(side="left", fill="x", expand=True)
        champ_libelle(col_op, "Opérateur").pack(anchor="w")
        self.entry_operateur = champ_entry(col_op)
        self.entry_operateur.pack(fill="x", ipady=5, pady=(4, 0))

        # État (affiché en modification uniquement)
        if est_modif:
            champ_libelle(card.corps, "État de l'étude").pack(anchor="w", pady=(8, 0))
            self.combo_etat = champ_combobox(
                card.corps,
                values=["en_cours", "termine"],
                state="readonly",
                width=20,
            )
            self.combo_etat.set(zone.etat or "en_cours")
            self.combo_etat.pack(anchor="w", ipady=4, pady=(4, 8))
        else:
            self.combo_etat = None

        champ_libelle(card.corps, "Localisation / description").pack(anchor="w", pady=(8, 0))
        self.text_description = champ_texte(card.corps, height=4)
        self.text_description.pack(fill="x", pady=(4, 0))

        # Pré-remplissage
        if est_modif:
            self._remplir()

        # --- Boutons ---
        separateur(contenu, height=1, bg=theme.BORDER).pack(fill="x", pady=20)
        barre = tk.Frame(contenu, bg=theme.BG)
        barre.pack(fill="x")

        bouton_secondaire(barre, "Annuler",
                          command=self.window.destroy).pack(side="left")
        texte_save = "Enregistrer les modifications" if est_modif else "Créer l'étude"
        bouton_accent(barre, texte_save,
                      command=self._enregistrer).pack(side="right")

    # ------------------------------------------------------------------
    def _champ(self, parent, label, obligatoire=False, attr=None):
        champ_libelle(parent, label, obligatoire=obligatoire).pack(anchor="w", pady=(8, 0))
        e = champ_entry(parent)
        e.pack(fill="x", ipady=5, pady=(4, 0))
        if attr:
            setattr(self, attr, e)

    def _remplir(self):
        z = self.zone
        self.entry_nom.insert(0, z.nom or "")
        self.entry_site.insert(0, z.site or "")
        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, z.date_campagne or "")
        self.entry_operateur.insert(0, z.operateur or "")
        if z.localisation:
            self.text_description.insert("1.0", z.localisation)

    def _enregistrer(self):
        nom = self.entry_nom.get().strip()
        site = self.entry_site.get().strip()
        date_c = self.entry_date.get().strip()
        operateur = self.entry_operateur.get().strip()
        desc = self.text_description.get("1.0", "end").strip()
        etat = self.combo_etat.get() if self.combo_etat else "en_cours"

        if not nom:
            messagebox.showerror("Champ obligatoire",
                                 "Le nom de l'étude est obligatoire.", parent=self.window)
            return
        if not site:
            messagebox.showerror("Champ obligatoire",
                                 "Le cours d'eau / site est obligatoire.", parent=self.window)
            return

        zone = Zone(nom=nom, site=site, date_campagne=date_c,
                    operateur=operateur, etat=etat,
                    localisation=desc, remarques="")

        try:
            if self.zone:
                zone.id = self.zone.id
                self.repo.modifier(zone)
            else:
                self.repo.ajouter(zone)
        except (sqlite3.IntegrityError, sqlite3.OperationalError,
                sqlite3.DatabaseError) as erreur:
            traiter_erreur_sqlite(erreur, self.window, "l'enregistrement de l'étude")
            return

        if self.refresh_callback:
            self.refresh_callback()
        self.window.destroy()
