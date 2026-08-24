"""Histogrammes HydroK."""

from ui import theme
from ui.charts.core import nouvelle_figure


def graphique_histogramme(valeurs, figsize=(6.2, 3.2), titre="Distribution des valeurs de K", xlabel="K (m/s)"):
    """Histogramme de répartition des valeurs de K."""
    fig, ax = nouvelle_figure(figsize=figsize)

    if not valeurs or len(valeurs) < 2:
        ax.text(
            0.5, 0.5, "Pas assez de données\npour un histogramme",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    nb_bins = max(4, min(10, len(valeurs) // 2))

    ax.hist(
        valeurs,
        bins=nb_bins,
        color=theme.ACCENT,
        edgecolor="white",
        linewidth=1.0,
        zorder=3,
    )

    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel("Effectif", fontsize=9)
    ax.set_title(
        titre, fontsize=10, fontweight="bold",
        color=theme.TEXT, pad=10, wrap=True,
    )
    ax.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))

    fig.tight_layout(pad=1.2)
    return fig
