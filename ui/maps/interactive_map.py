"""Carte OpenStreetMap interactive pour les points de mesure."""

from dataclasses import dataclass
import math
from queue import Empty, Queue
import threading
import tkinter as tk
from urllib.request import Request, urlopen

from ui import theme
from utils.logging_config import obtenir_logger

try:
    from tkintermapview import TkinterMapView
except ImportError:  # L'interface reste utilisable si l'installation est incomplète.
    TkinterMapView = None


logger = obtenir_logger(__name__)
URL_TUILES_OSM = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"


@dataclass(frozen=True)
class PointCarte:
    nom: str
    latitude: object
    longitude: object
    facies: object = None
    k_moyen: object = None


def normaliser_points(points):
    """Conserve les coordonnées numériques compatibles avec OpenStreetMap."""
    valides = []
    for point in points:
        try:
            latitude = float(point.latitude)
            longitude = float(point.longitude)
        except (TypeError, ValueError):
            logger.warning("Coordonnées GPS invalides pour le point %s", point.nom)
            continue
        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -85.0511 <= latitude <= 85.0511
            or not -180 <= longitude <= 180
        ):
            logger.warning("Coordonnées GPS hors limites pour le point %s", point.nom)
            continue
        valides.append((point, latitude, longitude))
    return valides


def calculer_emprise(points_valides):
    """Retourne les coins avec une marge utilisée par le zoom automatique."""
    if not points_valides:
        return None

    latitudes = [latitude for _, latitude, _ in points_valides]
    longitudes = [longitude for _, _, longitude in points_valides]
    latitude_min, latitude_max = min(latitudes), max(latitudes)
    longitude_min, longitude_max = min(longitudes), max(longitudes)

    ecart_latitude = latitude_max - latitude_min
    ecart_longitude = longitude_max - longitude_min
    marge_latitude = max(ecart_latitude * 0.08, 0.005)
    marge_longitude = max(ecart_longitude * 0.08, 0.005)

    coin_haut_gauche = (
        min(85.0511, latitude_max + marge_latitude),
        max(-180, longitude_min - marge_longitude),
    )
    coin_bas_droit = (
        max(-85.0511, latitude_min - marge_latitude),
        min(180, longitude_max + marge_longitude),
    )
    return coin_haut_gauche, coin_bas_droit


class CarteInteractive(tk.Frame):
    """Affiche les points d'une étude sur une carte OpenStreetMap."""

    def __init__(self, parent, hauteur=320, **kwargs):
        super().__init__(parent, bg=theme.SURFACE, height=hauteur, **kwargs)
        self.pack_propagate(False)
        self._marqueurs = []
        self._detruit = False
        self._fermeture_en_cours = False
        self._widget_detruit = False
        self._resultat_reseau = Queue(maxsize=1)
        self._rappel_reseau = None
        self._rappel_ajustement = None
        self._thread_reseau = None

        self._details = tk.StringVar(
            value=("Cliquez sur un marqueur pour afficher ses informations.  "
                   "© OpenStreetMap contributors")
        )
        self._message = tk.Label(
            self,
            bg=theme.SURFACE_ALT,
            fg=theme.TEXT_MUTED,
            font=theme.f_body(10),
            justify="center",
        )

        if TkinterMapView is None:
            self._carte = None
            self._afficher_message(
                "Carte interactive indisponible. Installez tkintermapview."
            )
            logger.error("tkintermapview n'est pas installé")
            return

        try:
            self._carte = TkinterMapView(self, corner_radius=0)
            self._carte.set_tile_server(URL_TUILES_OSM, max_zoom=19)
            self._carte.pack(fill="both", expand=True)
            tk.Label(
                self,
                textvariable=self._details,
                bg=theme.SURFACE,
                fg=theme.TEXT_MUTED,
                font=theme.f_small(9),
                justify="left",
                anchor="w",
                padx=10,
                pady=6,
            ).pack(fill="x")
            self._verifier_acces_tuiles()
        except (OSError, RuntimeError, tk.TclError):
            self._carte = None
            logger.exception("Impossible d'initialiser la carte OpenStreetMap")
            self._afficher_message(
                "La carte OpenStreetMap ne peut pas être affichée."
            )

    def actualiser(self, points):
        """Remplace les marqueurs et ajuste la vue aux coordonnées valides."""
        if self._fermeture_en_cours:
            return
        self._annuler_rappel("_rappel_ajustement")
        self._supprimer_marqueurs()
        points_valides = normaliser_points(points)
        if self._carte is None:
            return
        if not points_valides:
            self._afficher_message("Aucun point GPS disponible pour cette étude.")
            return

        self._message.place_forget()
        try:
            for point, latitude, longitude in points_valides:
                marqueur = self._carte.set_marker(
                    latitude,
                    longitude,
                    text=str(point.nom),
                    command=self._afficher_details,
                )
                marqueur.data = point
                self._marqueurs.append(marqueur)

            emprise = calculer_emprise(points_valides)
            self._rappel_ajustement = self.after_idle(
                lambda: self._executer_ajustement(emprise)
            )
        except (OSError, RuntimeError, tk.TclError):
            logger.exception("Impossible d'afficher les points sur la carte")
            self._afficher_message(
                "La carte OpenStreetMap ne peut pas être affichée."
            )

    def _supprimer_marqueurs(self):
        for marqueur in self._marqueurs:
            try:
                marqueur.delete()
            except (AttributeError, tk.TclError):
                logger.warning("Marqueur cartographique déjà supprimé")
        self._marqueurs.clear()

    def _ajuster_vue(self, emprise):
        if self._fermeture_en_cours or self._carte is None or emprise is None:
            return
        try:
            ajuster_immediatement = getattr(
                self._carte, "_fit_bounding_box", None
            )
            if callable(ajuster_immediatement):
                ajuster_immediatement(*emprise)
            else:
                self._carte.fit_bounding_box(*emprise)
        except (OSError, RuntimeError, tk.TclError):
            logger.exception("Impossible d'ajuster la carte aux points GPS")
            self._afficher_message(
                "La carte OpenStreetMap ne peut pas être affichée."
            )

    def _executer_ajustement(self, emprise):
        self._rappel_ajustement = None
        self._ajuster_vue(emprise)

    def _afficher_details(self, marqueur):
        if self._fermeture_en_cours:
            return
        point = marqueur.data
        try:
            latitude = float(point.latitude)
            longitude = float(point.longitude)
        except (TypeError, ValueError):
            return
        k_texte = theme.format_k(point.k_moyen)
        if k_texte != "—":
            k_texte = f"{k_texte} m/s"
        self._details.set(
            f"{point.nom}  ·  Latitude : {latitude:.6f}  ·  "
            f"Longitude : {longitude:.6f}  ·  "
            f"Faciès : {point.facies or '—'}  ·  K moyen : {k_texte}"
            "  ·  © OpenStreetMap contributors"
        )

    def _afficher_message(self, texte):
        if self._fermeture_en_cours:
            return
        self._message.configure(text=texte)
        self._message.place(relx=0.5, rely=0.5, anchor="center")
        self._message.lift()

    def _verifier_acces_tuiles(self):
        def verifier():
            try:
                requete = Request(
                    URL_TUILES_OSM.format(z=0, x=0, y=0),
                    headers={"User-Agent": "HydroK/1.0"},
                )
                with urlopen(requete, timeout=5):
                    self._resultat_reseau.put(None)
            except (OSError, TimeoutError) as erreur:
                logger.exception("Serveur de tuiles OpenStreetMap inaccessible")
                self._resultat_reseau.put(erreur)

        self._thread_reseau = threading.Thread(
            target=verifier,
            name="hydrok-osm-check",
            daemon=True,
        )
        self._thread_reseau.start()
        self._rappel_reseau = self.after(200, self._lire_resultat_reseau)

    def _lire_resultat_reseau(self):
        self._rappel_reseau = None
        if self._fermeture_en_cours:
            return
        try:
            erreur = self._resultat_reseau.get_nowait()
        except Empty:
            self._rappel_reseau = self.after(200, self._lire_resultat_reseau)
            return
        if erreur is not None:
            self._afficher_message(
                "La carte OpenStreetMap est temporairement indisponible."
            )

    def _annuler_rappel(self, attribut):
        rappel = getattr(self, attribut, None)
        if rappel is None:
            return
        try:
            self.after_cancel(rappel)
        except tk.TclError:
            logger.debug("Rappel cartographique déjà supprimé")
        setattr(self, attribut, None)

    def nettoyer_avant_fermeture(self):
        """Neutralise la carte et ses tâches sans détruire deux fois le cadre."""
        if self._fermeture_en_cours:
            return
        self._fermeture_en_cours = True
        self._detruit = True
        self._annuler_rappel("_rappel_reseau")
        self._annuler_rappel("_rappel_ajustement")
        self._supprimer_marqueurs()
        if self._carte is not None:
            self._carte.running = False
            self._annuler_rappels_carte_interne()
            getattr(self._carte, "image_load_queue_tasks", []).clear()
            getattr(self._carte, "image_load_queue_results", []).clear()
            try:
                self._carte.destroy()
            except tk.TclError:
                logger.debug("Carte OpenStreetMap déjà détruite")
            self._carte = None
        self._thread_reseau = None

    def _annuler_rappels_carte_interne(self):
        """Annule les ``after`` enregistrés par TkinterMapView lui-même."""
        carte = self._carte
        if carte is None:
            return
        commandes = set(getattr(carte, "_tclCommands", ()) or ())
        try:
            rappels = carte.tk.call("after", "info")
        except (AttributeError, tk.TclError):
            return
        for rappel in rappels:
            try:
                script = carte.tk.call("after", "info", rappel)[0]
                commande = str(script).split()[0]
                if commande in commandes:
                    carte.after_cancel(rappel)
            except (IndexError, tk.TclError):
                logger.debug("Rappel interne cartographique déjà supprimé")

    def destroy(self):
        if self._widget_detruit:
            return
        self.nettoyer_avant_fermeture()
        self._widget_detruit = True
        super().destroy()
