"""Génération d'une image OpenStreetMap statique pour les exports."""

import io
import math
from urllib.request import Request, urlopen

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from PIL import Image

from ui.maps.interactive_map import (
    URL_TUILES_OSM,
    calculer_emprise,
    normaliser_points,
)
from utils.logging_config import obtenir_logger


TAILLE_TUILE = 256
logger = obtenir_logger(__name__)


def _coordonnees_monde(latitude, longitude, zoom):
    echelle = TAILLE_TUILE * (2 ** zoom)
    x = (longitude + 180.0) / 360.0 * echelle
    sinus = math.sin(math.radians(latitude))
    y = (
        0.5 - math.log((1 + sinus) / (1 - sinus)) / (4 * math.pi)
    ) * echelle
    return x, y


def _coordonnees_geographiques(x, y, zoom):
    """Convertit des coordonnées Web Mercator en longitude/latitude."""
    echelle = TAILLE_TUILE * (2 ** zoom)
    longitude = x / echelle * 360.0 - 180.0
    latitude = math.degrees(math.atan(math.sinh(
        math.pi * (1.0 - 2.0 * y / echelle)
    )))
    return latitude, longitude


def _distance_horizontale_km(longitude_gauche, longitude_droite, latitude):
    """Approxime la largeur géographique visible à la latitude centrale."""
    return (
        abs(longitude_droite - longitude_gauche)
        * 111.320
        * math.cos(math.radians(latitude))
    )


def _longueur_echelle_km(largeur_km):
    """Choisit une longueur d'échelle lisible proche du cinquième de la carte."""
    cible = max(largeur_km / 5.0, 0.001)
    puissance = 10 ** math.floor(math.log10(cible))
    return max(
        valeur * puissance
        for valeur in (1, 2, 5, 10)
        if valeur * puissance <= cible
    )


def calculer_vue_osm(points_valides, largeur, hauteur, marge=24, zoom_max=19):
    """Calcule le centre et le zoom maximal contenant l'emprise commune."""
    emprise = calculer_emprise(points_valides)
    if emprise is None:
        return None
    haut_gauche, bas_droit = emprise
    zoom_retenu = 0
    for zoom in range(zoom_max + 1):
        gauche, haut = _coordonnees_monde(
            haut_gauche[0], haut_gauche[1], zoom
        )
        droite, bas = _coordonnees_monde(
            bas_droit[0], bas_droit[1], zoom
        )
        if (
            droite - gauche <= largeur - 2 * marge
            and bas - haut <= hauteur - 2 * marge
        ):
            zoom_retenu = zoom
        else:
            break

    gauche, haut = _coordonnees_monde(
        haut_gauche[0], haut_gauche[1], zoom_retenu
    )
    droite, bas = _coordonnees_monde(
        bas_droit[0], bas_droit[1], zoom_retenu
    )
    return (gauche + droite) / 2, (haut + bas) / 2, zoom_retenu


def _charger_tuile(zoom, x, y):
    url = URL_TUILES_OSM.format(z=zoom, x=x, y=y)
    requete = Request(url, headers={"User-Agent": "HydroK/1.0"})
    with urlopen(requete, timeout=5) as reponse:
        return Image.open(io.BytesIO(reponse.read())).convert("RGB")


def generer_carte_osm_png(points, largeur=900, hauteur=380):
    """Compose la carte OSM scientifique et retourne son PNG."""
    points_valides = normaliser_points(points)
    vue = calculer_vue_osm(points_valides, largeur, hauteur)
    if vue is None:
        raise ValueError("Aucun point GPS valide à afficher sur la carte.")

    centre_x, centre_y, zoom = vue
    haut_gauche, bas_droit = calculer_emprise(points_valides)
    gauche_emprise, haut_emprise = _coordonnees_monde(
        haut_gauche[0], haut_gauche[1], zoom
    )
    droite_emprise, bas_emprise = _coordonnees_monde(
        bas_droit[0], bas_droit[1], zoom
    )
    facteur_zoom = min(
        (largeur - 72) / max(droite_emprise - gauche_emprise, 1),
        (hauteur - 72) / max(bas_emprise - haut_emprise, 1),
        1.85,
    )
    facteur_zoom = max(1.0, facteur_zoom)
    origine_x = centre_x - largeur / (2 * facteur_zoom)
    origine_y = centre_y - hauteur / (2 * facteur_zoom)
    tuile_x_min = math.floor(origine_x / TAILLE_TUILE)
    tuile_y_min = math.floor(origine_y / TAILLE_TUILE)
    tuile_x_max = math.floor(
        (origine_x + largeur / facteur_zoom - 1) / TAILLE_TUILE
    )
    tuile_y_max = math.floor(
        (origine_y + hauteur / facteur_zoom - 1) / TAILLE_TUILE
    )
    nombre_tuiles = 2 ** zoom

    image = Image.new("RGB", (largeur, hauteur), "#E5E7EB")
    tuiles_chargees = 0
    derniere_erreur = None
    for tuile_x in range(tuile_x_min, tuile_x_max + 1):
        for tuile_y in range(tuile_y_min, tuile_y_max + 1):
            if not 0 <= tuile_y < nombre_tuiles:
                continue
            try:
                tuile = _charger_tuile(
                    zoom, tuile_x % nombre_tuiles, tuile_y
                )
            except (OSError, ValueError) as erreur:
                derniere_erreur = erreur
                continue
            tuiles_chargees += 1
            if facteur_zoom != 1.0:
                taille_redimensionnee = math.ceil(TAILLE_TUILE * facteur_zoom)
                tuile = tuile.resize(
                    (taille_redimensionnee, taille_redimensionnee),
                    Image.Resampling.LANCZOS,
                )
            image.paste(
                tuile,
                (
                    round((tuile_x * TAILLE_TUILE - origine_x) * facteur_zoom),
                    round((tuile_y * TAILLE_TUILE - origine_y) * facteur_zoom),
                ),
            )

    if tuiles_chargees == 0:
        logger.error(
            "Aucune tuile OpenStreetMap n'a pu être téléchargée",
            exc_info=derniere_erreur,
        )
        raise OSError(
            "Aucune tuile OpenStreetMap disponible pour la carte statique."
        ) from derniere_erreur

    latitude_haut, longitude_gauche = _coordonnees_geographiques(
        origine_x, origine_y, zoom
    )
    latitude_bas, longitude_droite = _coordonnees_geographiques(
        origine_x + largeur / facteur_zoom,
        origine_y + hauteur / facteur_zoom,
        zoom,
    )

    figure = Figure(figsize=(largeur / 100, hauteur / 100), dpi=100)
    canevas = FigureCanvasAgg(figure)
    axe = figure.add_axes((0.055, 0.13, 0.79, 0.84))
    axe.imshow(
        image,
        extent=(longitude_gauche, longitude_droite, latitude_bas, latitude_haut),
        origin="upper",
        aspect="auto",
        zorder=0,
    )

    valeurs_k = []
    for point, _, _ in points_valides:
        try:
            valeur = float(point.k_moyen)
        except (TypeError, ValueError):
            valeur = math.nan
        valeurs_k.append(valeur if math.isfinite(valeur) else math.nan)
    valeurs_finies = [valeur for valeur in valeurs_k if math.isfinite(valeur)]
    if valeurs_finies:
        minimum, maximum = min(valeurs_finies), max(valeurs_finies)
        if minimum == maximum:
            marge_k = abs(minimum) * 0.05 or 1.0
            minimum -= marge_k
            maximum += marge_k
        normalisation = Normalize(vmin=minimum, vmax=maximum)
    else:
        normalisation = Normalize(vmin=0.0, vmax=1.0)

    longitudes = [longitude for _, _, longitude in points_valides]
    latitudes = [latitude for _, latitude, _ in points_valides]
    couleurs = [
        valeur if math.isfinite(valeur) else normalisation.vmin
        for valeur in valeurs_k
    ]
    marqueurs = axe.scatter(
        longitudes, latitudes, c=couleurs, cmap="viridis", norm=normalisation,
        s=98, edgecolors="white", linewidths=1.8, zorder=3,
    )

    axe.set_xlabel("Longitude", fontsize=8)
    axe.set_ylabel("Latitude", fontsize=8)
    axe.tick_params(labelsize=7, direction="out", length=3)
    axe.ticklabel_format(useOffset=False, style="plain")
    axe.set_xlim(longitude_gauche, longitude_droite)
    axe.set_ylim(latitude_bas, latitude_haut)

    axe_couleurs = figure.add_axes((0.875, 0.20, 0.032, 0.69))
    barre_couleurs = figure.colorbar(marqueurs, cax=axe_couleurs)
    barre_couleurs.set_label("K moyen (m/s)", fontsize=9.5)
    barre_couleurs.ax.tick_params(labelsize=8.5)

    canevas.draw()
    rendu = canevas.get_renderer()
    boites_occupees = []
    centre_longitude = (longitude_gauche + longitude_droite) / 2
    centre_latitude = (latitude_haut + latitude_bas) / 2
    for point, latitude, longitude in points_valides:
        horizontal = 1 if longitude <= centre_longitude else -1
        vertical = 1 if latitude <= centre_latitude else -1
        candidats = (
            (10 * horizontal, 10 * vertical),
            (10 * horizontal, -18 * vertical),
            (-28 * horizontal, 10 * vertical),
            (-28 * horizontal, -18 * vertical),
            (0, 16 * vertical),
            (0, -22 * vertical),
            (32 * horizontal, 0),
            (-36 * horizontal, 0),
        )
        annotation_retenue = None
        for decalage_x, decalage_y in candidats:
            annotation = axe.annotate(
                str(point.nom), (longitude, latitude),
                xytext=(decalage_x, decalage_y), textcoords="offset points",
                ha="left" if decalage_x >= 0 else "right",
                va="bottom" if decalage_y >= 0 else "top",
                fontsize=9.5, color="#1F2937", clip_on=True, zorder=4,
                bbox={
                    "boxstyle": "round,pad=0.2", "facecolor": "white",
                    "edgecolor": "#6B7280", "linewidth": 0.6, "alpha": 0.9,
                },
            )
            boite = annotation.get_window_extent(renderer=rendu).expanded(1.08, 1.18)
            dans_carte = (
                boite.x0 >= axe.bbox.x0 and boite.x1 <= axe.bbox.x1
                and boite.y0 >= axe.bbox.y0 and boite.y1 <= axe.bbox.y1
            )
            sans_collision = not any(
                boite.overlaps(boite_occupee) for boite_occupee in boites_occupees
            )
            if dans_carte and sans_collision:
                annotation_retenue = annotation
                boites_occupees.append(boite)
                break
            annotation.remove()
        if annotation_retenue is None:
            annotation = axe.annotate(
                str(point.nom), (longitude, latitude), xytext=(8, 8),
                textcoords="offset points", fontsize=9.5, color="#1F2937",
                clip_on=True, zorder=4,
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "white",
                      "edgecolor": "#6B7280", "linewidth": 0.6, "alpha": 0.9},
            )
            boites_occupees.append(
                annotation.get_window_extent(renderer=rendu).expanded(1.08, 1.18)
            )

    latitude_centre = (latitude_haut + latitude_bas) / 2
    largeur_km = _distance_horizontale_km(
        longitude_gauche, longitude_droite, latitude_centre
    )
    echelle_km = _longueur_echelle_km(largeur_km)
    fraction = echelle_km / largeur_km
    x_depart, y_echelle = 0.055, 0.065
    axe.plot(
        (x_depart, x_depart + fraction), (y_echelle, y_echelle),
        transform=axe.transAxes, color="white", linewidth=4, zorder=4,
    )
    axe.plot(
        (x_depart, x_depart + fraction), (y_echelle, y_echelle),
        transform=axe.transAxes, color="#1F2937", linewidth=1.5, zorder=5,
    )
    axe.text(
        x_depart + fraction / 2, y_echelle + 0.022, f"{echelle_km:g} km",
        transform=axe.transAxes, ha="center", va="bottom", fontsize=7,
        color="#1F2937", zorder=5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8,
              "pad": 1},
    )
    axe.text(
        0.995, 0.012, "© OpenStreetMap contributors",
        transform=axe.transAxes, ha="right", va="bottom", fontsize=6.5,
        color="#374151", zorder=5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85,
              "pad": 1},
    )

    sortie = io.BytesIO()
    canevas.print_png(sortie)
    figure.clear()
    return sortie.getvalue()
