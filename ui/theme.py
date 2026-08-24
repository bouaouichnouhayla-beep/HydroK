"""Charte graphique commune de l'application HydroK."""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


# Palette

PRIMARY = "#155E75"          # bleu pétrole (couleur de marque)
PRIMARY_DARK = "#0B3C4D"     # bleu très foncé (en-têtes, sidebar)
PRIMARY_LIGHT = "#3B82A0"
PRIMARY_SOFT = "#E3EEF2"     # fond bleu très clair (survol, sélection)

ACCENT = "#0D9488"           # teal (boutons d'action, accents)
ACCENT_DARK = "#0F766E"
ACCENT_SOFT = "#E1F4F1"

BG = "#EEF2F4"                # fond général de l'application
SURFACE = "#FFFFFF"           # fond des cartes / panneaux
SURFACE_ALT = "#F7F9FA"       # fond légèrement teinté (zébrage, bandeaux)
BORDER = "#E0E5E9"
BORDER_STRONG = "#C7CFD6"

TEXT = "#1E2A32"
TEXT_MUTED = "#64727C"
TEXT_FAINT = "#94A1AA"
TEXT_ON_DARK = "#F5F8FA"
TEXT_ON_DARK_MUTED = "#AFC2CC"

SUCCESS = "#1F9D55"
SUCCESS_BG = "#E7F8EE"
DANGER = "#C0392B"
DANGER_DARK = "#9C2B20"
DANGER_BG = "#FBEAEA"
WARNING = "#B9770E"
WARNING_BG = "#FCF1DE"
INFO = "#2563A8"
INFO_BG = "#E8F1FB"

# Courbes, barres et séries.
CHART_PALETTE = [
    "#155E75",
    "#0D9488",
    "#B9770E",
    "#C0392B",
    "#6D5BA8",
    "#3F8F4F",
    "#C2598A",
    "#5C7A99",
]


def couleur_statut(etat: str) -> tuple:
    """Retourne (fond, texte) selon un état de zone."""
    etat = (etat or "").strip().lower()
    if etat in ("termine", "terminé", "termin\u00e9e", "termine_e", "cloture", "clôturé"):
        return (SUCCESS_BG, SUCCESS)
    if etat in ("en_cours", "en cours"):
        return (INFO_BG, INFO)
    return (WARNING_BG, WARNING)


# Polices

_FAMILY = "Segoe UI"
_FAMILY_RESOLVED = False


def init_fonts(root):
    """Sélectionne une police disponible lors du démarrage."""
    global _FAMILY, _FAMILY_RESOLVED

    if _FAMILY_RESOLVED:
        return

    try:
        disponibles = set(tkfont.families(root))
    except tk.TclError:
        disponibles = set()

    for candidate in ("Segoe UI", "Helvetica Neue", "Helvetica", "Liberation Sans", "Arial"):
        if candidate in disponibles:
            _FAMILY = candidate
            break
    else:
        _FAMILY = "TkDefaultFont"

    _FAMILY_RESOLVED = True


def font(size=10, bold=False, italic=False):
    """Construit un tuple de police conforme au thème."""
    style_parts = []
    if bold:
        style_parts.append("bold")
    if italic:
        style_parts.append("italic")

    if style_parts:
        return (_FAMILY, size, " ".join(style_parts))
    return (_FAMILY, size)


# Polices sémantiques

def f_titre_app(size=15):
    return font(size, bold=True)


def f_h1(size=20):
    return font(size, bold=True)


def f_h2(size=15):
    return font(size, bold=True)


def f_h3(size=12):
    return font(size, bold=True)


def f_label(size=9):
    return font(size, bold=True)


def f_body(size=10):
    return font(size)


def f_body_bold(size=10):
    return font(size, bold=True)


def f_small(size=9):
    return font(size)


def f_small_italic(size=9):
    return font(size, italic=True)


def f_mono(size=11, bold=False):
    return font(size, bold=bold)


def f_chiffre(size=22):
    return font(size, bold=True)


# Styles ttk

def apply_theme(root: tk.Tk):
    """Configure le thème de la fenêtre racine."""
    init_fonts(root)

    root.configure(bg=BG)
    root.option_add("*Font", font(10))
    root.option_add("*Background", BG)
    root.option_add("*Toplevel.Background", BG)

    style = ttk.Style(root)

    # "clam" permet de personnaliser toutes les couleurs ttk.
    try:
        style.theme_use("clam")
    except tk.TclError:
        # Conserve le thème actif si "clam" est indisponible.
        return style

    # Tableaux
    style.configure(
        "Treeview",
        background=SURFACE,
        fieldbackground=SURFACE,
        foreground=TEXT,
        rowheight=30,
        font=font(10),
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", PRIMARY_SOFT)],
        foreground=[("selected", PRIMARY_DARK)],
    )

    style.configure(
        "Treeview.Heading",
        background=PRIMARY,
        foreground=TEXT_ON_DARK,
        font=font(9, bold=True),
        relief="flat",
        borderwidth=0,
        padding=(10, 8),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", PRIMARY_DARK)],
    )

    # Barres de défilement
    style.configure(
        "Vertical.TScrollbar",
        background=BORDER_STRONG,
        troughcolor=BG,
        bordercolor=BG,
        arrowcolor=TEXT_MUTED,
        relief="flat",
        width=12,
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", TEXT_FAINT)],
    )

    # Listes déroulantes
    style.configure(
        "TCombobox",
        fieldbackground=SURFACE,
        background=SURFACE,
        foreground=TEXT,
        arrowcolor=PRIMARY,
        padding=6,
        relief="flat",
        font=font(10),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE)],
        bordercolor=[("focus", PRIMARY)],
    )
    root.option_add("*TCombobox*Listbox.font", font(10))
    root.option_add("*TCombobox*Listbox.selectBackground", PRIMARY_SOFT)
    root.option_add("*TCombobox*Listbox.selectForeground", PRIMARY_DARK)

    # Onglets
    style.configure(
        "TNotebook",
        background=BG,
        borderwidth=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=SURFACE_ALT,
        foreground=TEXT_MUTED,
        font=font(10, bold=True),
        padding=(16, 10),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", SURFACE)],
        foreground=[("selected", PRIMARY)],
    )

    # Barres de répartition
    style.configure(
        "Accent.Horizontal.TProgressbar",
        troughcolor=SURFACE_ALT,
        background=ACCENT,
        bordercolor=SURFACE_ALT,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
    )

    return style


def format_k(valeur):
    """Formate une conductivité en notation scientifique."""
    if valeur is None:
        return "—"
    try:
        return f"{float(valeur):.3e}"
    except (TypeError, ValueError):
        return "—"


def format_nombre(valeur, decimales=2):
    if valeur is None:
        return "—"
    try:
        return f"{float(valeur):.{decimales}f}"
    except (TypeError, ValueError):
        return "—"


def m_vers_cm(valeur_m):
    """Convertit en centimètres une valeur stockée en mètres."""
    if valeur_m is None:
        return None
    try:
        return float(valeur_m) * 100.0
    except (TypeError, ValueError):
        return None


def format_cm(valeur_m, decimales=1):
    """Formate en centimètres une longueur stockée en mètres."""
    cm = m_vers_cm(valeur_m)
    if cm is None:
        return "—"
    return f"{cm:.{decimales}f}"


def format_profondeurs_cm(chaine_m):
    """Convertit en centimètres une liste de profondeurs en mètres."""
    if not chaine_m or chaine_m == "—":
        return "—"
    parties = [p.strip() for p in chaine_m.split(",") if p.strip()]
    valeurs_cm = []
    for p in parties:
        try:
            valeurs_cm.append(f"{float(p) * 100:g}")
        except ValueError:
            valeurs_cm.append(p)
    return ", ".join(valeurs_cm) if valeurs_cm else "—"
