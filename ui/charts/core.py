"""Initialisation Matplotlib et création des figures HydroK."""

from utils.matplotlib_config import configurer_cache_matplotlib


# Doit précéder le premier import de Matplotlib pour éviter un cache inaccessible.
configurer_cache_matplotlib()

import matplotlib
matplotlib.use("Agg")  # remplacé dynamiquement par TkAgg si Tk est dispo

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    matplotlib.use("TkAgg")
except (ImportError, RuntimeError):  # pragma: no cover - environnement sans tkinter
    FigureCanvasTkAgg = None

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ui import theme


plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.edgecolor"] = theme.BORDER_STRONG
plt.rcParams["axes.labelcolor"] = theme.TEXT_MUTED
plt.rcParams["xtick.color"] = theme.TEXT_MUTED
plt.rcParams["ytick.color"] = theme.TEXT_MUTED
plt.rcParams["text.color"] = theme.TEXT
plt.rcParams["figure.facecolor"] = theme.SURFACE
plt.rcParams["axes.facecolor"] = theme.SURFACE
plt.rcParams["savefig.facecolor"] = theme.SURFACE


def nouvelle_figure(figsize=(5, 3.2), dpi=100):
    """Crée une figure + un unique axe, déjà mis en forme."""
    fig = Figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(theme.SURFACE)
    ax.set_facecolor(theme.SURFACE)

    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        ax.spines[spine_name].set_color(theme.BORDER_STRONG)

    ax.grid(axis="y", color=theme.BORDER, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8.5, length=0)

    return fig, ax
