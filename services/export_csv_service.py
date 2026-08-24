"""Exporte en CSV les données préparées par la synthèse tabulaire."""

import csv
from datetime import datetime
from pathlib import Path

from services.synthese_table_service import (
    LigneMaterielSynthese,
    SyntheseTableService,
)
from utils.logging_config import obtenir_logger

logger = obtenir_logger(__name__)


class ExportCsvService:
    """Sérialise les données de ``SyntheseTableService`` sans les recalculer."""

    COLONNES_REPETITIONS = (
        "Étude",
        "Point",
        "Latitude",
        "Longitude",
        "Faciès",
        "Méthode",
        "Numéro de répétition",
        "Profondeur h_p (m)",
        "Hauteur d'eau h_w (m)",
        "Hauteur d'air h_a (m)",
        "Volume d'eau (L)",
        "Hauteur début (m)",
        "Hauteur fin (m)",
        "Temps d'infiltration (s)",
        "Référence outil",
        "Référence sonde",
        "Conductivité hydraulique K (m/s)",
        "Commentaire",
    )
    COLONNES_OUTILS = (
        "Référence / nom",
        "Type",
        "Diamètre intérieur (cm)",
        "Hauteur (cm)",
        "L1 (cm)",
        "L2 (cm)",
        "D1 (cm)",
        "D2 (cm)",
        "D3 (cm)",
    )
    COLONNES_SONDES = (
        "Référence / nom",
        "Longueur totale (cm)",
        "Longueur de crépine (cm)",
        "Facteur C",
    )

    def __init__(self, synthese_table_service=None):
        self.synthese_table_service = (
            synthese_table_service or SyntheseTableService()
        )

    def exporter_repetitions_zone(self, zone_id: int, chemin) -> None:
        """Écrit une ligne par répétition de la zone dans ``chemin``."""
        donnees = self.synthese_table_service.pour_zone(zone_id)
        self._exporter_repetitions(donnees, chemin)

    def exporter_materiel_zone(self, zone_id: int, chemin) -> None:
        """Écrit une ligne sans doublon par matériel utilisé dans la zone."""
        donnees = self.synthese_table_service.pour_zone(zone_id)
        self._exporter_materiel(donnees, chemin)

    def exporter_zone(
        self, zone_id: int, nom_etude: str, dossier,
        *, ecraser: bool = False, instant=None,
    ) -> tuple[Path, Path]:
        """Génère les deux CSV horodatés d'une étude dans un dossier."""
        horodatage = (instant or datetime.now()).strftime("%Y-%m-%d_%H-%M")
        nom_fichier = self._nom_fichier(nom_etude)
        dossier = Path(dossier)
        chemin_repetitions = (
            dossier / f"{nom_fichier}_repetitions_{horodatage}.csv"
        )
        chemin_materiel = (
            dossier / f"{nom_fichier}_materiel_{horodatage}.csv"
        )

        chemins = (chemin_repetitions, chemin_materiel)
        if not ecraser and any(chemin.exists() for chemin in chemins):
            raise FileExistsError("Un export portant ce nom existe déjà.")

        donnees = self.synthese_table_service.pour_zone(zone_id)
        self._exporter_repetitions(donnees, chemin_repetitions)
        self._exporter_materiel(donnees, chemin_materiel)
        logger.info("Export CSV terminé dans %s", dossier)
        return chemins

    def _exporter_repetitions(self, donnees, chemin) -> None:
        lignes = (
            (
                ligne.nom_etude,
                ligne.nom_point,
                ligne.latitude,
                ligne.longitude,
                ligne.facies,
                ligne.methode,
                ligne.numero_repetition,
                ligne.profondeur_enfoncement,
                ligne.hauteur_eau,
                ligne.hauteur_air,
                ligne.volume_eau,
                ligne.h_debut,
                ligne.h_fin,
                ligne.temps_infiltration,
                ligne.nom_outil,
                ligne.nom_sonde,
                ligne.k_calcule,
                ligne.commentaire,
            )
            for ligne in donnees.repetitions
        )
        self._ecrire(chemin, self.COLONNES_REPETITIONS, lignes)

    def _exporter_materiel(self, donnees, chemin) -> None:
        outils = self._materiels_uniques(donnees.materiels, "outil")
        sondes = self._materiels_uniques(donnees.materiels, "sonde")

        with Path(chemin).open("w", encoding="utf-8", newline="") as fichier:
            writer = csv.writer(fichier, delimiter=";", lineterminator="\n")
            writer.writerow(("Outils utilisés",))
            writer.writerow(self.COLONNES_OUTILS)
            for ligne in outils:
                writer.writerow(self._ligne_outil(ligne))

            writer.writerow(())
            writer.writerow(("Sondes utilisées",))
            writer.writerow(self.COLONNES_SONDES)
            for ligne in sondes:
                writer.writerow(self._ligne_sonde(ligne))

    @staticmethod
    def _nom_fichier(nom_etude: str) -> str:
        """Remplace les séparateurs interdits sans altérer le nom affiché."""
        nom = str(nom_etude).strip()
        for caractere in ('/', '\\'):
            nom = nom.replace(caractere, "_")
        return nom or "Etude"

    @staticmethod
    def _ecrire(chemin, colonnes, lignes) -> None:
        """Crée un CSV UTF-8 séparé par des points-virgules."""
        with Path(chemin).open("w", encoding="utf-8", newline="") as fichier:
            writer = csv.writer(fichier, delimiter=";", lineterminator="\n")
            writer.writerow(colonnes)
            for ligne in lignes:
                writer.writerow("" if valeur is None else valeur for valeur in ligne)

    @staticmethod
    def _materiels_uniques(lignes, categorie):
        uniques = {}
        for ligne in lignes:
            if ligne.categorie == categorie:
                uniques.setdefault(ligne.materiel_id, ligne)
        return list(uniques.values())

    @staticmethod
    def _cm(valeur):
        return "" if valeur is None else f"{float(valeur) * 100:g}"

    @classmethod
    def _ligne_outil(cls, ligne: LigneMaterielSynthese):
        if ligne.type_materiel == "tuyau":
            return (
                ligne.nom,
                "Tuyau",
                cls._cm(ligne.diametre_interieur),
                cls._cm(ligne.hauteur),
                "", "", "", "", "",
            )
        return (
            ligne.nom,
            "Entonnoir",
            "", "",
            cls._cm(ligne.L1),
            cls._cm(ligne.L2),
            cls._cm(ligne.D1),
            cls._cm(ligne.D2),
            cls._cm(ligne.D3),
        )

    @classmethod
    def _ligne_sonde(cls, ligne: LigneMaterielSynthese):
        return (
            ligne.nom,
            cls._cm(ligne.longueur_totale),
            cls._cm(ligne.longueur_crepine),
            "" if ligne.facteur_c is None else ligne.facteur_c,
        )
