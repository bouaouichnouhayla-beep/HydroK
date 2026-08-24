"""Affichage commun des schémas redimensionnés dans un Canvas Tkinter."""

from pathlib import Path
import tkinter as tk

from PIL import Image, ImageTk, UnidentifiedImageError

from ui import theme
from ui.widgets import HeaderBar, bouton_secondaire
from utils.logging_config import obtenir_logger


logger = obtenir_logger(__name__)


class SchemaImage:
    """Charge et centre un schéma en conservant ses proportions."""

    def __init__(
        self, canvas, autoriser_agrandissement=True,
        adapter_a_toute_la_fenetre=False,
    ):
        self.canvas = canvas
        self.autoriser_agrandissement = autoriser_agrandissement
        self.adapter_a_toute_la_fenetre = adapter_a_toute_la_fenetre
        self._chemin = None
        self._image_source = None
        self._image_tk = None
        self._titre = None
        self._message = "Schéma indisponible"
        self._rafraichissement_id = None
        self.canvas.bind("<Configure>", self._planifier_rendu, add="+")
        if self.autoriser_agrandissement:
            self.canvas.bind("<Double-Button-1>", self._ouvrir_en_grand, add="+")

    def afficher(self, chemin, titre=None):
        """Affiche le fichier indiqué ou un message discret s'il est absent."""
        self._titre = titre
        self._chemin = Path(chemin)
        self._image_source = None
        self._message = "Schéma indisponible"
        try:
            if not self._chemin.is_file():
                raise FileNotFoundError(self._chemin)
            try:
                with Image.open(self._chemin) as image:
                    self._image_source = image.copy()
            except (UnidentifiedImageError, OSError):
                logger.exception("Image de schéma illisible : %s", self._chemin)
        except FileNotFoundError:
            logger.warning("Image de schéma absente : %s", self._chemin)
        self._rendre()

    def afficher_message(self, message):
        """Efface l'image et affiche une consigne dans le même emplacement."""
        self._image_source = None
        self._chemin = None
        self._titre = None
        self._message = message
        self._rendre()

    def _ouvrir_en_grand(self, event=None):
        """Ouvre une visionneuse redimensionnable pour le schéma courant."""
        if self._image_source is None or self._chemin is None:
            return
        SchemaViewer(
            parent=self.canvas,
            chemin=self._chemin,
            titre=self._titre or "Schéma",
        )

    def _planifier_rendu(self, event=None):
        if self._rafraichissement_id is not None:
            self.canvas.after_cancel(self._rafraichissement_id)
        self._rafraichissement_id = self.canvas.after_idle(self._rendre)

    def _rendre(self):
        self._rafraichissement_id = None
        if not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        largeur = max(self.canvas.winfo_width(), 40)
        hauteur = max(self.canvas.winfo_height(), 40)

        if self._image_source is None:
            self._image_tk = None
            self.canvas.create_text(
                largeur / 2, hauteur / 2,
                text=self._message,
                fill=theme.TEXT_FAINT,
                font=theme.f_small_italic(9),
                justify="center",
            )
            return

        marge = 16
        nombre_lignes = len(str(self._titre).splitlines()) if self._titre else 0
        espace_titre = 18 * nombre_lignes + 10 if self._titre else 0
        espace_indication = 22 if self.autoriser_agrandissement else 0
        image = self._image_source.copy()
        filtre = getattr(Image, "Resampling", Image).LANCZOS
        largeur_disponible = max(1, largeur - 2 * marge)
        hauteur_disponible = max(
            1, hauteur - 2 * marge - espace_titre - espace_indication
        )
        if self.adapter_a_toute_la_fenetre:
            facteur = min(
                largeur_disponible / image.width,
                hauteur_disponible / image.height,
            )
            image = image.resize(
                (max(1, round(image.width * facteur)),
                 max(1, round(image.height * facteur))),
                filtre,
            )
        else:
            image.thumbnail(
                (largeur_disponible, hauteur_disponible), filtre
            )
        self._image_tk = ImageTk.PhotoImage(image)
        centre_y = (hauteur - espace_titre - espace_indication) / 2
        self.canvas.create_image(
            largeur / 2, centre_y, image=self._image_tk, anchor="center"
        )
        if self._titre:
            self.canvas.create_text(
                largeur / 2, hauteur - 8 - espace_indication,
                text=self._titre,
                fill=theme.TEXT,
                font=theme.f_label(9),
                justify="center",
                anchor="s",
                width=max(1, largeur - 2 * marge),
            )
        if self.autoriser_agrandissement:
            self.canvas.create_text(
                largeur / 2, hauteur - 6,
                text="🔍 Double-cliquez sur le schéma pour l'agrandir.",
                fill=theme.TEXT_FAINT,
                font=theme.f_small_italic(8),
                justify="center",
                anchor="s",
                width=max(1, largeur - 2 * marge),
            )


class SchemaViewer:
    """Fenêtre commune d'affichage agrandi d'un schéma HydroK."""

    def __init__(self, parent, chemin, titre):
        self.window = tk.Toplevel(parent)
        self.window.title(f"HydroK — {titre}")
        self.window.geometry("1000x760")
        self.window.minsize(560, 420)
        self.window.configure(bg=theme.BG)
        self.window.resizable(True, True)
        self.window.transient(parent.winfo_toplevel())

        HeaderBar(
            self.window, ["HydroK", titre]
        ).pack(fill="x")

        contenu = tk.Frame(self.window, bg=theme.BG)
        contenu.pack(fill="both", expand=True, padx=24, pady=(20, 14))
        canvas = tk.Canvas(
            contenu, bg=theme.SURFACE,
            highlightbackground=theme.BORDER,
            highlightthickness=1, bd=0,
        )
        canvas.pack(fill="both", expand=True)
        self.schema = SchemaImage(
            canvas,
            autoriser_agrandissement=False,
            adapter_a_toute_la_fenetre=True,
        )
        self.schema.afficher(chemin, titre)

        barre = tk.Frame(self.window, bg=theme.BG)
        barre.pack(fill="x", padx=24, pady=(0, 18))
        bouton_secondaire(
            barre, "Fermer", command=self.window.destroy
        ).pack(side="right")
