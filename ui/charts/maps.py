"""Carte de points de mesure HydroK."""

from ui import theme
from ui.charts.core import nouvelle_figure


def graphique_carte_points(longitudes, latitudes, noms_points, valeurs_k=None, figsize=(6.2, 3.4)):
    """Carte simple latitude/longitude des points, colorée par K moyen si disponible."""
    fig, ax = nouvelle_figure(figsize=figsize)

    donnees = []
    for lon, lat, nom, k in zip(longitudes, latitudes, noms_points, valeurs_k or [None] * len(noms_points)):
        if lon is None or lat is None:
            continue
        try:
            donnees.append((float(lon), float(lat), nom, k))
        except (TypeError, ValueError):
            continue

    if not donnees:
        ax.text(
            0.5, 0.5, "Coordonnées GPS non renseignées",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    xs = [d[0] for d in donnees]
    ys = [d[1] for d in donnees]
    ks = [d[3] for d in donnees]

    if any(k is not None for k in ks):
        k_for_color = [k if k is not None else 0 for k in ks]
        scatter = ax.scatter(xs, ys, c=k_for_color, s=70, cmap="viridis", edgecolors="white", linewidths=0.9, zorder=3)
        cbar = fig.colorbar(scatter, ax=ax, shrink=0.82)
        cbar.set_label("K (m/s)", fontsize=9)
        cbar.ax.tick_params(labelsize=8.5)
    else:
        ax.scatter(xs, ys, color=theme.PRIMARY, s=70, edgecolors="white", linewidths=0.9, zorder=3)

    for x, y, nom, _ in donnees:
        ax.annotate(str(nom), (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8, color=theme.TEXT_MUTED)

    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    ax.set_title(
        "Localisation des points de mesure", fontsize=10,
        fontweight="bold", color=theme.TEXT, pad=10, wrap=True,
    )
    ax.ticklabel_format(useOffset=False, style="plain")

    fig.tight_layout(pad=1.2)
    return fig
