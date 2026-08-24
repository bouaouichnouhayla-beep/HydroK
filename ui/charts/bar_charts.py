"""Diagrammes en barres HydroK."""

import math

from ui import theme
from ui.charts.core import matplotlib, nouvelle_figure


def graphique_barres_k_par_point(noms_points, valeurs_k, ecarts_types=None, figsize=(6.2, 3.4)):
    """Diagramme en barres du K moyen par point de mesure, avec barres d'erreur."""
    fig, ax = nouvelle_figure(figsize=figsize)

    if not noms_points:
        ax.text(
            0.5, 0.5, "Pas encore de données",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    positions = range(len(noms_points))
    couleurs = [theme.CHART_PALETTE[i % len(theme.CHART_PALETTE)] for i in positions]

    ax.bar(
        positions,
        valeurs_k,
        yerr=ecarts_types if ecarts_types else None,
        color=couleurs,
        width=0.6,
        capsize=4,
        ecolor=theme.TEXT_FAINT,
        zorder=3,
    )

    ax.set_xticks(list(positions))
    ax.set_xticklabels(noms_points, fontsize=8.5)
    ax.set_ylabel("K moyen (m/s)", fontsize=9)
    ax.set_title("Conductivité hydraulique K moyenne par point", fontsize=10, fontweight="bold", color=theme.TEXT, pad=10)

    if valeurs_k:
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

    fig.tight_layout()
    return fig


def graphique_repetitions_par_profondeur(groupes, figsize=(6.2, 3.4)):
    """Compare les K des répétitions, regroupés par profondeur."""
    fig, ax = nouvelle_figure(figsize=figsize)

    groupes_valides = {
        profondeur: [k for k in valeurs_k if k is not None and k > 0]
        for profondeur, valeurs_k in groupes.items()
    }
    groupes_valides = {
        profondeur: mesures
        for profondeur, mesures in groupes_valides.items()
        if mesures
    }

    if not groupes_valides:
        ax.text(
            0.5, 0.5, "Pas encore de données",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    profondeurs = sorted(groupes_valides)
    if len(profondeurs) <= len(theme.CHART_PALETTE):
        couleurs = theme.CHART_PALETTE[:len(profondeurs)]
    else:
        palette = matplotlib.colormaps["tab20"].resampled(len(profondeurs))
        couleurs = [palette(index) for index in range(len(profondeurs))]

    nombre_series = len(profondeurs)
    nombre_repetitions = max(len(valeurs) for valeurs in groupes_valides.values())
    largeur_groupe = 0.78
    largeur_emplacement = largeur_groupe / nombre_series
    largeur_barre = largeur_emplacement * 0.82
    moyennes = []

    for index, (profondeur, couleur) in enumerate(zip(profondeurs, couleurs)):
        valeurs_serie = groupes_valides[profondeur]
        decalage = (index - (nombre_series - 1) / 2) * largeur_emplacement
        positions = [
            numero + decalage
            for numero in range(1, len(valeurs_serie) + 1)
        ]
        moyenne = sum(valeurs_serie) / len(valeurs_serie)
        libelle = f"h_p = {profondeur:g} cm (n = {len(valeurs_serie)})"

        ax.bar(
            positions, valeurs_serie,
            width=largeur_barre, color=couleur, label=libelle, zorder=3,
        )
        ax.axhline(
            moyenne, color=couleur, linewidth=1.4,
            linestyle="--", zorder=2,
        )
        moyennes.append((moyenne, couleur))

    ax.set_yscale("log")
    ax.set_xlim(0.45, nombre_repetitions + 0.55)
    ax.margins(y=0.12)

    borne_basse, borne_haute = ax.get_ylim()
    log_bas = math.log10(borne_basse)
    log_haut = math.log10(borne_haute)
    ecart_minimum = (log_haut - log_bas) * 0.07
    positions_libelles = []
    for moyenne, couleur in sorted(moyennes):
        position = math.log10(moyenne)
        if positions_libelles:
            position = max(position, positions_libelles[-1][0] + ecart_minimum)
        positions_libelles.append([position, moyenne, couleur])

    depassement = positions_libelles[-1][0] - log_haut
    if depassement > 0:
        for position in positions_libelles:
            position[0] -= depassement

    for position, moyenne, couleur in positions_libelles:
        moyenne_texte = f"{moyenne:.2e}".replace(".", ",")
        ax.annotate(
            f"K_moy = {moyenne_texte} m/s",
            xy=(1.0, moyenne), xycoords=("axes fraction", "data"),
            xytext=(1.035, 10 ** position),
            textcoords=("axes fraction", "data"),
            color=couleur, fontsize=7.5, va="center", ha="left",
            arrowprops={"arrowstyle": "-", "color": couleur, "lw": 0.8},
            annotation_clip=False,
        )

    numeros = list(range(1, nombre_repetitions + 1))
    ax.set_xticks(numeros)
    if nombre_repetitions > 15:
        ax.tick_params(axis="x", labelrotation=45, labelsize=7)
    ax.set_xlabel("N° de répétition", fontsize=9)
    ax.set_ylabel("K (m/s)", fontsize=9)
    fig.suptitle(
        "Conductivité hydraulique K par répétition et par profondeur",
        fontsize=10, fontweight="bold", color=theme.TEXT, y=0.98,
    )
    nombre_colonnes_legende = min(3, nombre_series)
    nombre_lignes_legende = math.ceil(nombre_series / nombre_colonnes_legende)
    fig.legend(
        *ax.get_legend_handles_labels(),
        loc="upper center", bbox_to_anchor=(0.41, 0.92),
        ncol=nombre_colonnes_legende, fontsize=7.5, frameon=False,
    )
    haut_axes = max(0.55, 0.79 - (nombre_lignes_legende - 1) * 0.06)
    fig.subplots_adjust(left=0.09, right=0.72, bottom=0.17, top=haut_axes)
    return fig


def graphique_repetitions_point(numeros, valeurs_k, aberrantes=None, moyenne=None, figsize=(6.2, 3.2)):
    """Évolution de K répétition par répétition pour un point donné, avec ligne de moyenne."""
    fig, ax = nouvelle_figure(figsize=figsize)

    if not numeros:
        ax.text(
            0.5, 0.5, "Aucune répétition saisie",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    aberrantes = aberrantes or [False] * len(numeros)
    couleurs = [theme.DANGER if a else theme.PRIMARY for a in aberrantes]

    ax.bar(numeros, valeurs_k, color=couleurs, width=0.55, zorder=3)

    valeur_max = max(valeurs_k) if valeurs_k else 0
    valeur_max = max(valeur_max, moyenne or 0)
    if valeur_max > 0:
        ax.set_ylim(0, valeur_max * 1.28)

    if moyenne is not None:
        ax.axhline(
            moyenne, color=theme.ACCENT_DARK, linewidth=1.6,
            linestyle="--", zorder=4, label=f"Moyenne = {moyenne:.2e} m/s",
        )
        ax.legend(loc="upper right", fontsize=8, frameon=False)

    ax.set_xlabel("N° de répétition", fontsize=9)
    ax.set_ylabel("K (m/s)", fontsize=9)
    ax.set_xticks(numeros)
    ax.set_title("Conductivité par répétition", fontsize=10, fontweight="bold", color=theme.TEXT, pad=10)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

    fig.tight_layout()
    return fig


def graphique_repartition_methodes(methodes, effectifs, figsize=(4.8, 3.2)):
    """Diagramme en barres de la répartition des répétitions par méthode."""
    fig, ax = nouvelle_figure(figsize=figsize)

    if not methodes or sum(effectifs) == 0:
        ax.text(
            0.5, 0.5, "Pas encore de données",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    positions = range(len(methodes))
    couleurs = [theme.CHART_PALETTE[i % len(theme.CHART_PALETTE)] for i in positions]

    ax.bar(positions, effectifs, color=couleurs, width=0.6, zorder=3)
    ax.set_xticks(list(positions))
    ax.set_xticklabels(methodes, fontsize=8.5)
    ax.set_ylabel("Nombre de répétitions", fontsize=9)
    ax.set_title(
        "Répartition des méthodes utilisées", fontsize=10,
        fontweight="bold", color=theme.TEXT, pad=10, wrap=True,
    )

    for pos, val in zip(positions, effectifs):
        ax.text(pos, val, str(val), ha="center", va="bottom", fontsize=8, color=theme.TEXT_MUTED)

    ax.yaxis.get_major_locator().set_params(integer=True)
    fig.tight_layout(pad=1.2)
    return fig


def graphique_repartition_profondeurs(profondeurs_cm, effectifs, figsize=(4.8, 3.2)):
    """Diagramme en barres des profondeurs échantillonnées dans la zone."""
    fig, ax = nouvelle_figure(figsize=figsize)

    if not profondeurs_cm or sum(effectifs) == 0:
        ax.text(
            0.5, 0.5, "Pas encore de données",
            ha="center", va="center", color=theme.TEXT_FAINT, fontsize=10,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    labels = [f"{p:g}" for p in profondeurs_cm]
    positions = range(len(labels))
    couleurs = [theme.CHART_PALETTE[i % len(theme.CHART_PALETTE)] for i in positions]

    ax.bar(positions, effectifs, color=couleurs, width=0.6, zorder=3)
    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_xlabel("Profondeur (cm)", fontsize=9)
    ax.set_ylabel("Nombre de répétitions", fontsize=9)
    ax.set_title(
        "Répartition des profondeurs mesurées", fontsize=10,
        fontweight="bold", color=theme.TEXT, pad=10, wrap=True,
    )

    for pos, val in zip(positions, effectifs):
        ax.text(pos, val, str(val), ha="center", va="bottom", fontsize=8, color=theme.TEXT_MUTED)

    ax.yaxis.get_major_locator().set_params(integer=True)
    fig.tight_layout(pad=1.2)
    return fig
