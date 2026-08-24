"""Diagrammes en secteurs HydroK."""

from ui import theme
from ui.charts.core import Figure


def graphique_repartition_facies(libelles, effectifs, figsize=(4.6, 3.4)):
    """Diagramme en secteurs de la répartition des points par faciès."""
    fig = Figure(figsize=figsize, dpi=100)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(theme.SURFACE)
    ax.set_facecolor(theme.SURFACE)

    if not libelles or sum(effectifs) == 0:
        ax.text(
            0.5, 0.5, "Pas encore de données",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis("off")
        return fig

    couleurs = [theme.CHART_PALETTE[i % len(theme.CHART_PALETTE)] for i in range(len(libelles))]

    ax.pie(
        effectifs,
        labels=libelles,
        autopct="%1.0f%%",
        startangle=90,
        colors=couleurs,
        textprops={"fontsize": 8.5, "color": theme.TEXT},
        wedgeprops={"edgecolor": theme.SURFACE, "linewidth": 1.5},
    )
    ax.set_title(
        "Répartition des points par faciès", fontsize=10,
        fontweight="bold", color=theme.TEXT, pad=10, wrap=True,
    )
    ax.axis("equal")

    fig.tight_layout(pad=1.2)
    return fig
