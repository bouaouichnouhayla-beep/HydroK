"""Boxplots HydroK."""

from ui import theme
from ui.charts.core import nouvelle_figure


def graphique_boxplot_k_par_point(noms_points, valeurs_par_point, figsize=(6.2, 3.4)):
    """Boxplot des valeurs de K par point : médiane, dispersion et valeurs extrêmes."""
    fig, ax = nouvelle_figure(figsize=figsize)

    donnees = [vals for vals in valeurs_par_point if vals]
    labels = [nom for nom, vals in zip(noms_points, valeurs_par_point) if vals]

    if not donnees:
        ax.text(
            0.5, 0.5, "Pas assez de données\npour le boxplot",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    bp = ax.boxplot(
        donnees,
        labels=labels,
        patch_artist=True,
        showmeans=True,
        meanline=True,
    )

    for i, boite in enumerate(bp["boxes"]):
        boite.set_facecolor(theme.CHART_PALETTE[i % len(theme.CHART_PALETTE)])
        boite.set_alpha(0.75)
        boite.set_edgecolor(theme.BORDER_STRONG)

    for element in ("whiskers", "caps", "medians", "means"):
        for ligne in bp[element]:
            ligne.set_color(theme.TEXT_MUTED)
            ligne.set_linewidth(1.1)

    for flier in bp["fliers"]:
        flier.set_marker("o")
        flier.set_markerfacecolor(theme.DANGER)
        flier.set_markeredgecolor("white")
        flier.set_markersize(4)

    ax.set_ylabel("K (m/s)", fontsize=9)
    ax.set_title(
        "Dispersion de K par point", fontsize=10, fontweight="bold",
        color=theme.TEXT, pad=10, wrap=True,
    )
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax.tick_params(axis="x", labelrotation=20)

    fig.tight_layout(pad=1.2)
    return fig
