"""Construction et remplissage du formulaire de répétition."""

import tkinter as tk

from ui import theme
from ui.repetition.constants import CM_VERS_M
from ui.schema_image import SchemaImage
from ui.widgets import (
    ScrollableFrame, HeaderBar, Card,
    bouton_accent, bouton_secondaire, bouton_primaire,
    champ_libelle, champ_entry, champ_texte, champ_combobox, separateur,
)


class RepetitionFormMixin:

    def _construire_interface(self, parent, est_modif, titre_page):
        self.window = tk.Toplevel(parent)
        self.window.title(f"HydroK — {titre_page}")
        self.window.geometry("1150x760")
        self.window.configure(bg=theme.BG)
        self.window.grab_set()
        self.window.resizable(True, True)
        self.window.minsize(950, 620)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)

        HeaderBar(self.window, ["HydroK", "Répétitions", titre_page]).pack(fill="x")

        sf = ScrollableFrame(self.window, bg=theme.BG)
        sf.pack(fill="both", expand=True)

        racine = tk.Frame(sf.contenu, bg=theme.BG)
        racine.pack(fill="both", expand=True, padx=30, pady=22)

        tk.Label(racine, text=titre_page, bg=theme.BG,
                 fg=theme.TEXT, font=theme.f_h1(20)).pack(anchor="w")
        tk.Label(racine,
                 text="Toutes les longueurs sont saisies en CENTIMÈTRES (cm).",
                 bg=theme.BG, fg=theme.TEXT_MUTED,
                 font=theme.f_small(9)).pack(anchor="w", pady=(2, 16))

        cols_frame = tk.Frame(racine, bg=theme.BG)
        cols_frame.pack(fill="both", expand=True)

        gauche = tk.Frame(cols_frame, bg=theme.BG)
        gauche.pack(side="left", fill="both", expand=True, padx=(0, 14))

        droite = tk.Frame(cols_frame, bg=theme.BG, width=360)
        droite.pack(side="right", fill="y")
        droite.pack_propagate(False)

        card_mat = Card(gauche, titre="Matériel utilisé", padding=18)
        card_mat.pack(fill="x", pady=(0, 14))

        champ_libelle(card_mat.corps, "Sonde piézométrique",
                      obligatoire=True).pack(anchor="w")
        self.sonde_var = tk.StringVar()
        self.combo_sonde = champ_combobox(card_mat.corps,
                                          textvariable=self.sonde_var,
                                          values=list(self.sonde_map.keys()),
                                          state="readonly")
        self.combo_sonde.pack(fill="x", ipady=4, pady=(4, 12))

        champ_libelle(card_mat.corps, "Outil utilisé",
                      obligatoire=True).pack(anchor="w")
        self.outil_var = tk.StringVar()
        self.combo_outil = champ_combobox(card_mat.corps,
                                          textvariable=self.outil_var,
                                          values=list(self.outil_map.keys()),
                                          state="readonly")
        self.combo_outil.pack(fill="x", ipady=4, pady=(4, 0))
        self.combo_outil.bind("<<ComboboxSelected>>", self._on_outil_change)

        card_mes = Card(gauche, titre="Mesures de terrain (en cm)", padding=18)
        card_mes.pack(fill="both", expand=True)

        self.entries = {}
        champs = [
            ("hauteur_eau",            "h_w  —  hauteur eau ext. (cm)",   False),
            ("profondeur_enfoncement", "h_p  —  profondeur enf. (cm)",    False),
            ("hauteur_air",            "h_a  —  hauteur d'air (cm)",      True),
            ("temps_infiltration",     "Temps d'infiltration (s)",        True),
            ("volume_eau",             "Volume d'eau (L)  [Entonnoir]",   False),
            ("h_debut",                "h début (cm)  [Tuyau]",           False),
            ("h_fin",                  "h fin (cm)  [Tuyau]",             False),
        ]

        grille = tk.Frame(card_mes.corps, bg=theme.SURFACE)
        grille.pack(fill="x")
        grille.columnconfigure(0, weight=1)
        grille.columnconfigure(1, weight=1)

        self.blocs_champs = {}
        for idx, (cle, label, obligatoire) in enumerate(champs):
            col = idx % 2
            row = idx // 2
            bloc = tk.Frame(grille, bg=theme.SURFACE)
            bloc.grid(row=row, column=col, sticky="ew",
                      padx=(0, 10) if col == 0 else (10, 0), pady=(0, 10))
            champ_libelle(bloc, label, obligatoire=obligatoire).pack(anchor="w")
            e = champ_entry(bloc)
            e.pack(fill="x", ipady=5, pady=(4, 0))
            self.blocs_champs[cle] = bloc
            self.entries[cle] = e

        self._mettre_a_jour_champs(None)

        champ_libelle(card_mes.corps, "Commentaire").pack(anchor="w", pady=(10, 0))
        self.commentaire_text = champ_texte(card_mes.corps, height=3)
        self.commentaire_text.pack(fill="x", pady=(4, 0))

        card_res = Card(droite, titre="Calcul de K", padding=18)
        card_res.pack(fill="x", pady=(0, 14))

        self.k_frame = tk.Frame(card_res.corps, bg=theme.PRIMARY_DARK, height=90)
        self.k_frame.pack(fill="x", pady=(0, 14))
        self.k_frame.pack_propagate(False)

        self.k_label = tk.Label(
            self.k_frame,
            text="—",
            bg=theme.PRIMARY_DARK,
            fg=theme.TEXT_ON_DARK,
            font=theme.f_chiffre(22),
        )
        self.k_label.pack(expand=True)

        self.k_unite = tk.Label(
            self.k_frame,
            text="m/s",
            bg=theme.PRIMARY_DARK,
            fg=theme.TEXT_ON_DARK_MUTED,
            font=theme.f_body(9),
        )
        self.k_unite.pack(pady=(0, 8))

        bouton_accent(card_res.corps, "⟳  Calculer K",
                      command=self._calculer_k).pack(fill="x", pady=(0, 8))

        separateur(card_res.corps, height=1, bg=theme.BORDER).pack(fill="x", pady=10)
        self.bouton_enregistrer = bouton_primaire(
            card_res.corps,
            "Enregistrer la répétition",
            command=self._enregistrer,
        )
        self.bouton_enregistrer.pack(fill="x")

        self.confirmation_label = tk.Label(
            card_res.corps,
            text="",
            bg=theme.SURFACE,
            fg=theme.SUCCESS,
            font=theme.f_small(9),
        )
        self.confirmation_label.pack(anchor="w", pady=(6, 0))

        card_schema = Card(droite, titre="Méthode de mesure", padding=14)
        card_schema.pack(fill="both", expand=True)

        self.canvas_schema = tk.Canvas(
            card_schema.corps, width=300, height=320,
            bg=theme.SURFACE, highlightthickness=0, bd=0,
        )
        self.canvas_schema.pack(fill="both", expand=True)
        self.schema_methode = SchemaImage(self.canvas_schema)
        self._dessiner_schema(None)

        separateur(racine, height=1, bg=theme.BORDER).pack(fill="x", pady=(18, 12))
        barre_bas = tk.Frame(racine, bg=theme.BG)
        barre_bas.pack(fill="x")
        bouton_secondaire(barre_bas, "Fermer",
                          command=self.window.destroy).pack(side="left")

        if est_modif:
            self._remplir()
        elif self.k_calcule is not None:
            self.k_label.configure(text=theme.format_k(self.k_calcule))

    def _remplir(self):
        rep = self.repetition

        for cle, s in self.sonde_map.items():
            if rep.sonde_id is not None and int(s.id) == int(rep.sonde_id):
                self.sonde_var.set(cle)
                break

        for cle, o in self.outil_map.items():
            if rep.outil_id is not None and o.id == rep.outil_id:
                self.outil_var.set(cle)
                break

        champs_val_m = {
            "profondeur_enfoncement": rep.profondeur_enfoncement,
            "hauteur_eau":            rep.hauteur_eau,
            "hauteur_air":            rep.hauteur_air,
            "h_debut":                rep.h_debut,
            "h_fin":                  rep.h_fin,
        }
        for cle, val_m in champs_val_m.items():
            if val_m is not None:
                self.entries[cle].insert(0, f"{val_m / CM_VERS_M:g}")

        if rep.temps_infiltration is not None:
            self.entries["temps_infiltration"].insert(0, str(rep.temps_infiltration))
        if rep.volume_eau is not None:
            self.entries["volume_eau"].insert(0, str(rep.volume_eau))

        if rep.commentaire:
            self.commentaire_text.insert("1.0", rep.commentaire)

        if rep.k_calcule is not None:
            self.k_calcule = rep.k_calcule
            self.k_label.configure(text=theme.format_k(rep.k_calcule))

        self._on_outil_change()
