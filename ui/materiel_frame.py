import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
from pathlib import Path

from repositories.sonde_repository import SondeRepository
from repositories.outil_repository import OutilRepository
from ui.sonde_dialog import SondeDialog
from ui.outil_dialog import OutilDialog
from ui import theme
from ui.error_handler import traiter_erreur_sqlite
from ui.schema_image import SchemaImage
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card,
    bouton_primaire, bouton_secondaire, bouton_danger,
    configurer_zebrage, inserer_ligne,
)

CM_VERS_M = 0.01
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = BASE_DIR / "assets" / "schemas"


class MaterielFrame(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller
        self.sonde_repo = SondeRepository()
        self.outil_repo = OutilRepository()

        # Référence gardée en mémoire pour éviter que Tkinter supprime l'image.
        self.photo_materiel = None

        self._build()

    def nettoyer(self):
        self.sf.detruire_proprement()

    def refresh(self):
        self._charger_sondes()
        self._charger_outils()
        self._afficher_message_photo("Sélectionnez une sonde ou un outil")

    # ------------------------------------------------------------------
    def _build(self):
        HeaderBar(self, ["HydroK", "Matériel"],
                  on_retour=self.controller.show_home).pack(fill="x")

        self.sf = ScrollableFrame(self, bg=theme.BG)
        self.sf.pack(fill="both", expand=True)

        racine = tk.Frame(self.sf.contenu, bg=theme.BG)
        racine.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(racine, text="Gestion du matériel",
                 bg=theme.BG, fg=theme.TEXT, font=theme.f_h1(22)).pack(
            anchor="w", pady=(0, 24)
        )

        # Mise en page principale : tableaux à gauche, photo à droite.
        contenu = tk.Frame(racine, bg=theme.BG)
        contenu.pack(fill="both", expand=True)

        gauche = tk.Frame(contenu, bg=theme.BG)
        gauche.pack(side="left", fill="both", expand=True, padx=(0, 18))

        droite = tk.Frame(contenu, bg=theme.BG, width=330)
        droite.pack(side="right", fill="y")
        droite.pack_propagate(False)

        self._build_panneau_photo(droite)

        # ---- Sondes ----
        haut_s = tk.Frame(gauche, bg=theme.BG)
        haut_s.pack(fill="x", pady=(0, 8))
        tk.Label(haut_s, text="Sondes piézométriques",
                 bg=theme.BG, fg=theme.TEXT,
                 font=theme.f_h3(14)).pack(side="left")
        bouton_primaire(haut_s, "+ Nouvelle sonde",
                        command=self._creer_sonde).pack(side="right", pady=4)

        card_s = Card(gauche, padding=0)
        card_s.pack(fill="x", pady=(0, 28))

        tb_s = tk.Frame(card_s.corps, bg=theme.SURFACE)
        tb_s.pack(fill="x", padx=16, pady=12)
        bouton_secondaire(tb_s, "✎  Modifier",
                          command=self._modifier_sonde).pack(side="left")
        bouton_danger(tb_s, "✕  Supprimer",
                      command=self._supprimer_sonde).pack(side="right")
        tk.Frame(card_s.corps, bg=theme.BORDER, height=1).pack(fill="x")

        cols_s = ("nom", "long_totale", "diam_int", "long_crepine")
        self.table_sondes = ttk.Treeview(card_s.corps, columns=cols_s,
                                         show="headings", height=8,
                                         selectmode="browse")
        configurer_zebrage(self.table_sondes)
        for col, label, w in [
            ("nom",          "Nom de la sonde",       220),
            ("long_totale",  "Long. totale (cm)",     140),
            ("diam_int",     "Ø intérieur (cm)",      140),
            ("long_crepine", "Long. crépine (cm)",    140),
        ]:
            self.table_sondes.heading(col, text=label)
            self.table_sondes.column(col, width=w, anchor="center")

        vsb_s = ttk.Scrollbar(card_s.corps, orient="vertical",
                              command=self.table_sondes.yview)
        self.table_sondes.configure(yscrollcommand=vsb_s.set)
        self.table_sondes.pack(side="left", fill="x", expand=True,
                               padx=(16, 0), pady=(0, 16))
        vsb_s.pack(side="right", fill="y", pady=(0, 16), padx=(0, 6))

        self.table_sondes.bind("<<TreeviewSelect>>", self._on_sonde_select)

        # ---- Outils ----
        haut_o = tk.Frame(gauche, bg=theme.BG)
        haut_o.pack(fill="x", pady=(0, 8))
        tk.Label(haut_o, text="Outils de mesure",
                 bg=theme.BG, fg=theme.TEXT,
                 font=theme.f_h3(14)).pack(side="left")
        bouton_primaire(haut_o, "+ Nouvel outil",
                        command=self._creer_outil).pack(side="right", pady=4)

        card_o = Card(gauche, padding=0)
        card_o.pack(fill="x")

        tb_o = tk.Frame(card_o.corps, bg=theme.SURFACE)
        tb_o.pack(fill="x", padx=16, pady=12)
        bouton_secondaire(tb_o, "✎  Modifier",
                          command=self._modifier_outil).pack(side="left")
        bouton_danger(tb_o, "✕  Supprimer",
                      command=self._supprimer_outil).pack(side="right")
        tk.Frame(card_o.corps, bg=theme.BORDER, height=1).pack(fill="x")

        cols_o = ("nom", "type", "d_int", "h_tuyau", "l1", "l2", "d1", "d2", "d3")
        self.table_outils = ttk.Treeview(card_o.corps, columns=cols_o,
                                         show="headings", height=8,
                                         selectmode="browse")
        configurer_zebrage(self.table_outils)
        for col, label, w in [
            ("nom",     "Nom de l'outil",      180),
            ("type",    "Type",                 95),
            ("d_int",   "Ø tuyau (cm)",         95),
            ("h_tuyau", "H. tuyau (cm)",        95),
            ("l1",      "L1 (cm)",              70),
            ("l2",      "L2 (cm)",              70),
            ("d1",      "D1 (cm)",              70),
            ("d2",      "D2 (cm)",              70),
            ("d3",      "D3 (cm)",              70),
        ]:
            self.table_outils.heading(col, text=label)
            self.table_outils.column(col, width=w, anchor="center")

        vsb_o = ttk.Scrollbar(card_o.corps, orient="vertical",
                              command=self.table_outils.yview)
        self.table_outils.configure(yscrollcommand=vsb_o.set)
        self.table_outils.pack(side="left", fill="x", expand=True,
                               padx=(16, 0), pady=(0, 16))
        vsb_o.pack(side="right", fill="y", pady=(0, 16), padx=(0, 6))

        self.table_outils.bind("<<TreeviewSelect>>", self._on_outil_select)

        self._charger_sondes()
        self._charger_outils()
        self._afficher_message_photo("Sélectionnez une sonde ou un outil")

    # ------------------------------------------------------------------
    # Panneau photo
    # ------------------------------------------------------------------
    def _build_panneau_photo(self, parent):
        card_photo = Card(parent, titre="Matériel sélectionné", padding=14)
        card_photo.pack(fill="both", expand=True)

        self.photo_canvas = tk.Canvas(
            card_photo.corps,
            width=300,
            height=360,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self.photo_canvas.pack(fill="both", expand=True)
        self.schema_materiel = SchemaImage(self.photo_canvas)

    def _afficher_message_photo(self, message):
        self.schema_materiel.afficher_message(message)

    def _afficher_photo(self, fichier, titre):
        self.schema_materiel.afficher(SCHEMAS_DIR / fichier, titre)

    def _on_sonde_select(self, event=None):
        selection = self.table_sondes.selection()
        if selection:
            valeurs = self.table_sondes.item(selection[0], "values")
            if valeurs:
                self._afficher_photo(
                    "sonde.png", f"Sonde piézométrique\n{valeurs[0]}"
                )

    def _on_outil_select(self, event=None):
        sel = self.table_outils.selection()
        if not sel:
            return

        valeurs = self.table_outils.item(sel[0], "values")
        if not valeurs:
            return

        nom = valeurs[0]
        type_outil = valeurs[1]

        if type_outil == "tuyau":
            self._afficher_photo("tuyau.png", f"Tuyau\n{nom}")
        else:
            self._afficher_photo("entonnoir.png", f"Entonnoir\n{nom}")

    # ------------------------------------------------------------------
    def _charger_sondes(self):
        for r in self.table_sondes.get_children():
            self.table_sondes.delete(r)
        for i, s in enumerate(self.sonde_repo.lister()):
            long_totale_cm = f"{s.longueur_totale / CM_VERS_M:g}" if s.longueur_totale else "—"
            diam_cm = f"{s.diametre_interieur / CM_VERS_M:g}" if s.diametre_interieur else "—"
            crepine_cm = f"{s.longueur_crepine / CM_VERS_M:g}" if s.longueur_crepine else "—"
            inserer_ligne(self.table_sondes, i, str(s.id),
                          (s.nom, long_totale_cm, diam_cm, crepine_cm))

    def _charger_outils(self):
        for r in self.table_outils.get_children():
            self.table_outils.delete(r)

        def cm(v):
            return f"{v / CM_VERS_M:g}" if v is not None else "—"

        for i, o in enumerate(self.outil_repo.lister()):
            if o.type_outil == "tuyau":
                ligne = (o.nom, o.type_outil,
                         cm(o.diametre_interieur), cm(o.hauteur_tuyau),
                         "—", "—", "—", "—", "—")
            else:
                ligne = (o.nom, o.type_outil,
                         "—", "—",
                         cm(o.L1), cm(o.L2), cm(o.D1), cm(o.D2), cm(o.D3))
            inserer_ligne(self.table_outils, i, str(o.id), ligne)

    def _sel_sonde(self):
        sel = self.table_sondes.selection()
        return int(sel[0]) if sel else None

    def _sel_outil(self):
        sel = self.table_outils.selection()
        return int(sel[0]) if sel else None

    # Sondes
    def _creer_sonde(self):
        SondeDialog(self, refresh_callback=self._charger_sondes)

    def _modifier_sonde(self):
        sid = self._sel_sonde()
        if sid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une sonde.")
            return
        s = self.sonde_repo.trouver_par_id(sid)
        if s:
            SondeDialog(self, refresh_callback=self._charger_sondes, sonde=s)

    def _supprimer_sonde(self):
        sid = self._sel_sonde()
        if sid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord une sonde.")
            return
        if messagebox.askyesno("Supprimer", "Supprimer cette sonde ?"):
            try:
                self.sonde_repo.supprimer(sid)
            except (sqlite3.IntegrityError, sqlite3.OperationalError,
                    sqlite3.DatabaseError) as erreur:
                traiter_erreur_sqlite(erreur, self, "la suppression de la sonde")
                return
            self._charger_sondes()
            self._afficher_message_photo("Sélectionnez une sonde ou un outil")

    # Outils
    def _creer_outil(self):
        OutilDialog(self, refresh_callback=self._charger_outils)

    def _modifier_outil(self):
        oid = self._sel_outil()
        if oid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord un outil.")
            return
        o = self.outil_repo.trouver_par_id(oid)
        if o:
            OutilDialog(self, refresh_callback=self._charger_outils, outil=o)

    def _supprimer_outil(self):
        oid = self._sel_outil()
        if oid is None:
            messagebox.showinfo("HydroK", "Sélectionnez d'abord un outil.")
            return
        if messagebox.askyesno("Supprimer", "Supprimer cet outil ?"):
            try:
                self.outil_repo.supprimer(oid)
            except (sqlite3.IntegrityError, sqlite3.OperationalError,
                    sqlite3.DatabaseError) as erreur:
                traiter_erreur_sqlite(erreur, self, "la suppression de l'outil")
                return
            self._charger_outils()
            self._afficher_message_photo("Sélectionnez une sonde ou un outil")
