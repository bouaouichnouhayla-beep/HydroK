"""Widgets Tkinter partagés par l'interface HydroK."""

import tkinter as tk
from tkinter import ttk

from ui import theme


# Conteneur défilable

class ScrollableFrame(tk.Frame):
    """Cadre dont les widgets enfants sont ajoutés dans ``contenu``."""

    def __init__(self, parent, bg=None, **kwargs):
        bg = bg or theme.BG
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
            style="Vertical.TScrollbar",
        )

        self.contenu = tk.Frame(self.canvas, bg=bg)

        self._ajustement_geometry_id = None
        self._scrollbar_visible = True

        self._window = self.canvas.create_window(
            (0, 0), window=self.contenu, anchor="nw"
        )

        self.contenu.bind("<Configure>", self._on_contenu_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", self._activer_molette)
        self.canvas.bind("<Leave>", self._desactiver_molette)

    # Redimensionnement

    def _on_contenu_configure(self, event):
        """Demande un ajustement quand la taille du contenu change."""
        self._planifier_ajustement_geometry()

    def _on_canvas_configure(self, event):
        """Garde le contenu à la largeur du canevas."""
        self.canvas.itemconfig(self._window, width=event.width)
        # Réévalue la barre et la position après un redimensionnement.
        self._planifier_ajustement_geometry()

    def _planifier_ajustement_geometry(self):
        """Regroupe plusieurs changements de taille en un seul ajustement."""
        if self._ajustement_geometry_id is None:
            self._ajustement_geometry_id = self.after_idle(
                self._ajuster_scrollbar
            )

    def _ajuster_scrollbar(self):
        """Met à jour la zone défilable et la visibilité de la barre."""
        self._ajustement_geometry_id = None
        bbox = self.canvas.bbox("all")
        if bbox is None:
            return

        # La zone défilable suit toujours la taille réelle du contenu.
        self.canvas.configure(scrollregion=bbox)

        hauteur_contenu = bbox[3] - bbox[1]
        hauteur_canvas = self.canvas.winfo_height()
        scrollbar_necessaire = hauteur_contenu > hauteur_canvas

        if not scrollbar_necessaire and self._scrollbar_visible:
            self.scrollbar.pack_forget()
            self._scrollbar_visible = False
            self.canvas.yview_moveto(0)
        elif scrollbar_necessaire and not self._scrollbar_visible:
            self.scrollbar.pack(side="right", fill="y")
            self._scrollbar_visible = True

    # Molette multiplateforme

    def _activer_molette(self, event=None):
        """Active la molette lorsque le pointeur entre dans le canevas."""
        self.canvas.bind_all("<MouseWheel>", self._sur_molette_windows)
        self.canvas.bind_all("<Button-4>", self._sur_molette_linux)
        self.canvas.bind_all("<Button-5>", self._sur_molette_linux)

    def _desactiver_molette(self, event=None):
        """Retire les liaisons globales quand le pointeur quitte le canevas."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _peut_defiler(self):
        """Indique si le contenu dépasse la hauteur visible."""
        bbox = self.canvas.bbox("all")
        if bbox is None:
            return False
        hauteur_contenu = bbox[3] - bbox[1]
        return hauteur_contenu > self.canvas.winfo_height()

    def _sur_molette_windows(self, event):
        """Gère la molette sous Windows et macOS."""
        if not self.canvas.winfo_exists() or not self._peut_defiler():
            return
        # Windows utilise des multiples de 120, macOS des valeurs plus petites.
        pas = int(-1 * (event.delta / 120)) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
        self.canvas.yview_scroll(pas, "units")

    def _sur_molette_linux(self, event):
        """Gère les événements de molette utilisés sous Linux."""
        if not self.canvas.winfo_exists() or not self._peut_defiler():
            return
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def detruire_proprement(self):
        """À appeler avant de détruire le widget pour libérer les bindings globaux."""
        if self._ajustement_geometry_id is not None:
            self.after_cancel(self._ajustement_geometry_id)
            self._ajustement_geometry_id = None
        self._desactiver_molette()


# Boutons

def _bouton_hover(bouton, couleur_normale, couleur_survol):
    """Ajoute un changement de couleur au survol d'un bouton."""
    def on_enter(event):
        if str(bouton["state"]) != "disabled":
            bouton.configure(bg=couleur_survol)

    def on_leave(event):
        if str(bouton["state"]) != "disabled":
            bouton.configure(bg=couleur_normale)

    bouton.bind("<Enter>", on_enter)
    bouton.bind("<Leave>", on_leave)


def bouton_primaire(parent, text, command=None, width=None, **kwargs):
    """Bouton d'action principale (fond foncé)."""
    bouton = tk.Button(
        parent,
        text=text,
        command=command,
        bg=theme.PRIMARY,
        fg=theme.TEXT_ON_DARK,
        activebackground=theme.PRIMARY_DARK,
        activeforeground=theme.TEXT_ON_DARK,
        font=theme.f_body_bold(10),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=16,
        pady=8,
        width=width,
        **kwargs,
    )
    _bouton_hover(bouton, theme.PRIMARY, theme.PRIMARY_DARK)
    return bouton


def bouton_accent(parent, text, command=None, width=None, **kwargs):
    """Bouton d'action positive (validation, calcul, enregistrement)."""
    bouton = tk.Button(
        parent,
        text=text,
        command=command,
        bg=theme.ACCENT,
        fg=theme.TEXT_ON_DARK,
        activebackground=theme.ACCENT_DARK,
        activeforeground=theme.TEXT_ON_DARK,
        font=theme.f_body_bold(10),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=16,
        pady=8,
        width=width,
        **kwargs,
    )
    _bouton_hover(bouton, theme.ACCENT, theme.ACCENT_DARK)
    return bouton


def bouton_secondaire(parent, text, command=None, width=None, **kwargs):
    """Bouton d'action secondaire (fond clair, bordure)."""
    bouton = tk.Button(
        parent,
        text=text,
        command=command,
        bg=theme.SURFACE,
        fg=theme.TEXT,
        activebackground=theme.SURFACE_ALT,
        activeforeground=theme.TEXT,
        font=theme.f_body_bold(10),
        relief="solid",
        bd=1,
        highlightbackground=theme.BORDER_STRONG,
        cursor="hand2",
        padx=16,
        pady=7,
        width=width,
        **kwargs,
    )
    _bouton_hover(bouton, theme.SURFACE, theme.SURFACE_ALT)
    return bouton


def bouton_danger(parent, text, command=None, width=None, **kwargs):
    """Bouton de suppression / action destructrice."""
    bouton = tk.Button(
        parent,
        text=text,
        command=command,
        bg=theme.SURFACE,
        fg=theme.DANGER,
        activebackground=theme.DANGER_BG,
        activeforeground=theme.DANGER_DARK,
        font=theme.f_body_bold(10),
        relief="solid",
        bd=1,
        highlightbackground=theme.BORDER_STRONG,
        cursor="hand2",
        padx=16,
        pady=7,
        width=width,
        **kwargs,
    )
    _bouton_hover(bouton, theme.SURFACE, theme.DANGER_BG)
    return bouton


def bouton_texte(parent, text, command=None, **kwargs):
    """Bouton discret type lien (retour, annuler...)."""
    bouton = tk.Button(
        parent,
        text=text,
        command=command,
        bg=theme.BG,
        fg=theme.TEXT_MUTED,
        activebackground=theme.BG,
        activeforeground=theme.PRIMARY,
        font=theme.f_body_bold(10),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=8,
        pady=6,
        **kwargs,
    )

    def on_enter(event):
        bouton.configure(fg=theme.PRIMARY)

    def on_leave(event):
        bouton.configure(fg=theme.TEXT_MUTED)

    bouton.bind("<Enter>", on_enter)
    bouton.bind("<Leave>", on_leave)
    return bouton


# En-tête de page

class HeaderBar(tk.Frame):
    """Bandeau commun avec fil d'Ariane et bouton de retour."""

    def __init__(self, parent, fil_ariane, on_retour=None, **kwargs):
        super().__init__(parent, bg=theme.PRIMARY_DARK, height=52, **kwargs)
        self.pack_propagate(False)

        gauche = tk.Frame(self, bg=theme.PRIMARY_DARK)
        gauche.pack(side="left", fill="y", padx=18)

        self._construire_fil_ariane(gauche, fil_ariane)

        if on_retour is not None:
            droite = tk.Frame(self, bg=theme.PRIMARY_DARK)
            droite.pack(side="right", fill="y", padx=14)

            bouton = tk.Button(
                droite,
                text="←  Retour",
                command=on_retour,
                bg=theme.PRIMARY_DARK,
                fg=theme.TEXT_ON_DARK_MUTED,
                activebackground=theme.PRIMARY,
                activeforeground=theme.TEXT_ON_DARK,
                font=theme.f_body_bold(9),
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=10,
            )
            bouton.pack(side="right", pady=10)

            def on_enter(event):
                bouton.configure(fg=theme.TEXT_ON_DARK)

            def on_leave(event):
                bouton.configure(fg=theme.TEXT_ON_DARK_MUTED)

            bouton.bind("<Enter>", on_enter)
            bouton.bind("<Leave>", on_leave)

    def _construire_fil_ariane(self, parent, fil_ariane):
        """Affiche les étapes du fil d'Ariane dans leur ordre."""
        ligne = tk.Frame(parent, bg=theme.PRIMARY_DARK)
        ligne.pack(side="left", anchor="center", expand=True)

        for i, segment in enumerate(fil_ariane):
            est_dernier = i == len(fil_ariane) - 1

            tk.Label(
                ligne,
                text=segment,
                bg=theme.PRIMARY_DARK,
                fg=theme.TEXT_ON_DARK if est_dernier else theme.TEXT_ON_DARK_MUTED,
                font=theme.f_body_bold(11) if est_dernier else theme.f_body(11),
            ).pack(side="left")

            if not est_dernier:
                tk.Label(
                    ligne,
                    text="  ›  ",
                    bg=theme.PRIMARY_DARK,
                    fg=theme.TEXT_ON_DARK_MUTED,
                    font=theme.f_body(11),
                ).pack(side="left")


# Cartes

class Card(tk.Frame):
    """Panneau avec une bordure légère et un titre facultatif."""

    def __init__(self, parent, titre=None, padding=18, **kwargs):
        super().__init__(
            parent,
            bg=theme.SURFACE,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
            bd=0,
            **kwargs,
        )

        self.corps = tk.Frame(self, bg=theme.SURFACE)

        if titre:
            entete = tk.Frame(self, bg=theme.SURFACE)
            entete.pack(fill="x", padx=padding, pady=(padding, 6))

            tk.Label(
                entete,
                text=titre,
                bg=theme.SURFACE,
                fg=theme.TEXT,
                font=theme.f_h3(11),
            ).pack(side="left")

            tk.Frame(self, bg=theme.BORDER, height=1).pack(fill="x", padx=padding)

            self.corps.pack(fill="both", expand=True, padx=padding, pady=(10, padding))
        else:
            self.corps.pack(fill="both", expand=True, padx=padding, pady=padding)


class StatCard(tk.Frame):
    """Carte utilisée pour afficher un indicateur important."""

    def __init__(self, parent, titre, valeur, sous_texte=None, couleur=None, **kwargs):
        couleur = couleur or theme.PRIMARY
        super().__init__(
            parent,
            bg=theme.SURFACE,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
            bd=0,
            **kwargs,
        )

        liseret = tk.Frame(self, bg=couleur, width=4)
        liseret.pack(side="left", fill="y")

        corps = tk.Frame(self, bg=theme.SURFACE)
        corps.pack(side="left", fill="both", expand=True, padx=(14, 16), pady=14)

        tk.Label(
            corps,
            text=titre.upper(),
            bg=theme.SURFACE,
            fg=theme.TEXT_MUTED,
            font=theme.f_label(8),
        ).pack(anchor="w")

        self.label_valeur = tk.Label(
            corps,
            text=str(valeur),
            bg=theme.SURFACE,
            fg=theme.TEXT,
            font=theme.f_chiffre(19),
        )
        self.label_valeur.pack(anchor="w", pady=(4, 0))

        if sous_texte:
            tk.Label(
                corps,
                text=sous_texte,
                bg=theme.SURFACE,
                fg=theme.TEXT_FAINT,
                font=theme.f_small(8),
            ).pack(anchor="w", pady=(2, 0))

    def maj_valeur(self, valeur):
        """Met à jour la valeur sans reconstruire la carte."""
        self.label_valeur.configure(text=str(valeur))


def badge(parent, texte, fond, couleur_texte, **kwargs):
    """Petite étiquette colorée (ex. état d'une zone, mesure aberrante...)."""
    cadre = tk.Frame(parent, bg=fond, **kwargs)
    tk.Label(
        cadre,
        text=texte,
        bg=fond,
        fg=couleur_texte,
        font=theme.f_label(8),
        padx=10,
        pady=3,
    ).pack()
    return cadre


class EmptyState(tk.Frame):
    """Message affiché lorsqu'un tableau ou une liste est vide."""

    def __init__(self, parent, icone="—", titre="Aucune donnée", sous_texte="", **kwargs):
        super().__init__(parent, bg=theme.SURFACE_ALT, **kwargs)

        contenu = tk.Frame(self, bg=theme.SURFACE_ALT)
        contenu.pack(pady=36)

        tk.Label(
            contenu,
            text=icone,
            bg=theme.SURFACE_ALT,
            fg=theme.TEXT_FAINT,
            font=theme.font(28),
        ).pack()

        tk.Label(
            contenu,
            text=titre,
            bg=theme.SURFACE_ALT,
            fg=theme.TEXT_MUTED,
            font=theme.f_body_bold(11),
        ).pack(pady=(8, 2))

        if sous_texte:
            tk.Label(
                contenu,
                text=sous_texte,
                bg=theme.SURFACE_ALT,
                fg=theme.TEXT_FAINT,
                font=theme.f_small(9),
            ).pack()


# Champs de formulaire

def champ_libelle(parent, texte, obligatoire=False, **kwargs):
    """Libellé de champ de formulaire, harmonisé."""
    texte_complet = texte + (" *" if obligatoire else "")
    return tk.Label(
        parent,
        text=texte_complet,
        bg=kwargs.pop("bg", theme.SURFACE),
        fg=theme.TEXT_MUTED,
        font=theme.f_label(8),
        **kwargs,
    )


def champ_entry(parent, **kwargs):
    """Champ de saisie texte harmonisé."""
    return tk.Entry(
        parent,
        font=theme.f_body(10),
        bg=theme.SURFACE,
        fg=theme.TEXT,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=theme.BORDER,
        highlightcolor=theme.PRIMARY,
        insertbackground=theme.TEXT,
        **kwargs,
    )


def champ_texte(parent, height=4, **kwargs):
    """Zone de texte multilignes harmonisée."""
    return tk.Text(
        parent,
        height=height,
        font=theme.f_body(10),
        bg=theme.SURFACE,
        fg=theme.TEXT,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=theme.BORDER,
        highlightcolor=theme.PRIMARY,
        insertbackground=theme.TEXT,
        wrap="word",
        padx=8,
        pady=6,
        **kwargs,
    )


def champ_combobox(parent, **kwargs):
    """Crée une liste déroulante avec la police de l'application."""
    return ttk.Combobox(parent, font=theme.f_body(10), **kwargs)


def separateur(parent, **kwargs):
    """Crée une ligne de séparation discrète."""
    couleur = kwargs.pop("bg", theme.BORDER)
    hauteur = kwargs.pop("height", 1)
    return tk.Frame(parent, bg=couleur, height=hauteur, **kwargs)


def titre_section(parent, texte, **kwargs):
    """Crée le titre principal d'une section."""
    bg = kwargs.pop("bg", theme.BG)
    return tk.Label(
        parent,
        text=texte,
        bg=bg,
        fg=theme.TEXT,
        font=theme.f_h2(16),
        **kwargs,
    )


def sous_titre(parent, texte, **kwargs):
    """Crée un texte secondaire dans une section."""
    bg = kwargs.pop("bg", theme.BG)
    return tk.Label(
        parent,
        text=texte,
        bg=bg,
        fg=theme.TEXT_MUTED,
        font=theme.f_body(10),
        **kwargs,
    )


# Mise en forme des tableaux

def configurer_zebrage(tableau: ttk.Treeview):
    """Configure des bandes alternées + une teinte pour les lignes aberrantes."""
    tableau.tag_configure("paire", background=theme.SURFACE_ALT)
    tableau.tag_configure("impaire", background=theme.SURFACE)
    tableau.tag_configure(
        "aberrante", background=theme.DANGER_BG, foreground=theme.DANGER_DARK
    )


def inserer_ligne(tableau: ttk.Treeview, index, iid, values, aberrante=False):
    """Insère une ligne dans un Treeview avec zébrage automatique."""
    if aberrante:
        tag = "aberrante"
    else:
        tag = "paire" if index % 2 == 0 else "impaire"

    tableau.insert("", "end", iid=iid, values=values, tags=(tag,))
