import tkinter as tk
import sqlite3
from tkinter import messagebox

from models import PointMesure
from repositories.point_repository import PointRepository
from ui import theme
from ui.error_handler import traiter_erreur_sqlite
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card,
    bouton_accent, bouton_secondaire,
    champ_libelle, champ_entry, champ_texte, champ_combobox, separateur,
)

FACIES_LISTE = ["radier", "mouille", "plat", "rapide", "cascade", "berge", "autre"]


class PointDialog:

    def __init__(self, parent, zone_id, refresh_callback=None, point=None):
        self.zone_id = zone_id
        self.refresh_callback = refresh_callback
        self.point = point
        self.repo = PointRepository()

        est_modif = point is not None
        titre_page = "Modifier le point" if est_modif else "Nouveau point de mesure"

        self.window = tk.Toplevel(parent)
        self.window.title(f"HydroK — {titre_page}")
        self.window.geometry("620x560")
        self.window.configure(bg=theme.BG)
        self.window.grab_set()
        self.window.resizable(True, True)
        self.window.minsize(520, 460)

        HeaderBar(self.window,
                  ["HydroK", "Points", titre_page]).pack(fill="x")

        sf = ScrollableFrame(self.window, bg=theme.BG)
        sf.pack(fill="both", expand=True)

        contenu = tk.Frame(sf.contenu, bg=theme.BG)
        contenu.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(contenu, text=titre_page,
                 bg=theme.BG, fg=theme.TEXT, font=theme.f_h1(20)).pack(anchor="w")
        tk.Label(contenu, text="Les champs marqués * sont obligatoires.",
                 bg=theme.BG, fg=theme.TEXT_MUTED, font=theme.f_small(9)).pack(
                 anchor="w", pady=(4, 16))

        card = Card(contenu, titre="Identification du point", padding=20)
        card.pack(fill="x")

        # Nom
        champ_libelle(card.corps, "Nom du point", obligatoire=True).pack(anchor="w")
        self.entry_nom = champ_entry(card.corps)
        self.entry_nom.pack(fill="x", ipady=5, pady=(4, 12))

        # Faciès
        champ_libelle(card.corps, "Faciès hydraulique").pack(anchor="w")
        self.combo_facies = champ_combobox(card.corps, values=FACIES_LISTE, state="normal")
        self.combo_facies.pack(fill="x", ipady=4, pady=(4, 12))

        # Lat / Lon
        row_coord = tk.Frame(card.corps, bg=theme.SURFACE)
        row_coord.pack(fill="x", pady=(0, 12))

        col_lat = tk.Frame(row_coord, bg=theme.SURFACE)
        col_lat.pack(side="left", fill="x", expand=True, padx=(0, 8))
        champ_libelle(col_lat, "Latitude (N)").pack(anchor="w")
        self.entry_lat = champ_entry(col_lat)
        self.entry_lat.pack(fill="x", ipady=5, pady=(4, 0))

        col_lon = tk.Frame(row_coord, bg=theme.SURFACE)
        col_lon.pack(side="left", fill="x", expand=True)
        champ_libelle(col_lon, "Longitude (E)").pack(anchor="w")
        self.entry_lon = champ_entry(col_lon)
        self.entry_lon.pack(fill="x", ipady=5, pady=(4, 0))

        # Commentaires
        champ_libelle(card.corps, "Commentaires").pack(anchor="w", pady=(4, 0))
        self.text_commentaires = champ_texte(card.corps, height=3)
        self.text_commentaires.pack(fill="x", pady=(4, 0))

        if est_modif:
            self._remplir()

        separateur(contenu, height=1, bg=theme.BORDER).pack(fill="x", pady=20)
        barre = tk.Frame(contenu, bg=theme.BG)
        barre.pack(fill="x")

        bouton_secondaire(barre, "Annuler",
                          command=self.window.destroy).pack(side="left")
        texte_save = "Enregistrer les modifications" if est_modif else "Créer le point"
        bouton_accent(barre, texte_save,
                      command=self._enregistrer).pack(side="right")

    def _remplir(self):
        p = self.point
        self.entry_nom.insert(0, p.nom or "")
        self.combo_facies.set(p.facies or "")
        if p.latitude is not None:
            self.entry_lat.insert(0, str(p.latitude))
        if p.longitude is not None:
            self.entry_lon.insert(0, str(p.longitude))
        if p.commentaires:
            self.text_commentaires.insert("1.0", p.commentaires)

    def _enregistrer(self):
        nom = self.entry_nom.get().strip()
        facies = self.combo_facies.get().strip()
        lat_raw = self.entry_lat.get().strip()
        lon_raw = self.entry_lon.get().strip()
        commentaires = self.text_commentaires.get("1.0", "end").strip()

        if not nom:
            messagebox.showerror("Champ obligatoire",
                                 "Le nom du point est obligatoire.", parent=self.window)
            return

        try:
            latitude = float(lat_raw) if lat_raw else None
            longitude = float(lon_raw) if lon_raw else None
        except ValueError:
            messagebox.showerror("Valeur invalide",
                                 "Les coordonnées doivent être des nombres décimaux.",
                                 parent=self.window)
            return

        point = PointMesure(
            zone_id=int(self.zone_id),
            nom=nom, facies=facies,
            latitude=latitude, longitude=longitude,
            commentaires=commentaires
        )

        try:
            if self.point:
                point.id = self.point.id
                self.repo.modifier(point)
            else:
                self.repo.ajouter(point)

            if self.refresh_callback:
                self.refresh_callback()
            self.window.destroy()

        except (sqlite3.IntegrityError, sqlite3.OperationalError,
                sqlite3.DatabaseError) as erreur:
            traiter_erreur_sqlite(erreur, self.window, "l'enregistrement du point")
