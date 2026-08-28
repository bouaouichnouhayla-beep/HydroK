"""Export portable d'une étude HydroK au format ``.hydrok``."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from database.connection import DB_PATH
from repositories.outil_repository import OutilRepository
from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository
from repositories.sonde_repository import SondeRepository
from repositories.zone_repository import ZoneRepository
from version import APPLICATION_VERSION


def _zone_dict(zone):
    return {
        "id": zone.id,
        "nom": zone.nom,
        "site": zone.site,
        "localisation": zone.localisation,
        "date_campagne": zone.date_campagne,
        "operateur": zone.operateur,
        "etat": zone.etat,
        "remarques": zone.remarques,
    }


def _point_dict(point):
    return {
        "id": point.id,
        "zone_id": point.zone_id,
        "nom": point.nom,
        "latitude": point.latitude,
        "longitude": point.longitude,
        "facies": point.facies,
        "commentaires": point.commentaires,
    }


def _repetition_dict(repetition):
    return {
        "id": repetition.id,
        "point_id": repetition.point_id,
        "sonde_id": repetition.sonde_id,
        "outil_id": repetition.outil_id,
        "methode": repetition.methode,
        "profondeur_enfoncement": repetition.profondeur_enfoncement,
        "hauteur_eau": repetition.hauteur_eau,
        "hauteur_air": repetition.hauteur_air,
        "temps_infiltration": repetition.temps_infiltration,
        "volume_eau": repetition.volume_eau,
        "h_debut": repetition.h_debut,
        "h_fin": repetition.h_fin,
        "k_calcule": repetition.k_calcule,
        "commentaire": repetition.commentaire,
    }


def _sonde_dict(sonde):
    return {
        "id": sonde.id,
        "nom": sonde.nom,
        "longueur_totale": sonde.longueur_totale,
        "diametre_interieur": sonde.diametre_interieur,
        "longueur_crepine": sonde.longueur_crepine,
    }


def _outil_dict(outil):
    donnees = {
        "id": outil.id,
        "nom": outil.nom,
        "type_outil": outil.type_outil,
        "L1": None,
        "L2": None,
        "D1": None,
        "D2": None,
        "D3": None,
        "diametre_interieur": None,
        "hauteur_tuyau": None,
    }
    if outil.type_outil == "entonnoir":
        for nom in ("L1", "L2", "D1", "D2", "D3"):
            donnees[nom] = getattr(outil, nom)
    else:
        donnees["diametre_interieur"] = outil.diametre_interieur
        donnees["hauteur_tuyau"] = outil.hauteur_tuyau
    return donnees


def export_etude(etude_id, destination, *, db_path=DB_PATH):
    """Exporte la zone ``etude_id`` et toutes ses données liées.

    ``etude_id`` correspond à l'identifiant de la table ``zone``. Les
    identifiants inclus dans le fichier ne sont que des références internes
    à l'export et ne préjugent pas de ceux d'une future base importée.
    """
    zone_repo = ZoneRepository(db_path)
    point_repo = PointRepository(db_path)
    repetition_repo = RepetitionRepository(db_path)
    sonde_repo = SondeRepository(db_path)
    outil_repo = OutilRepository(db_path)

    zone = zone_repo.trouver_par_id(etude_id)
    if zone is None:
        raise ValueError(f"Étude introuvable : {etude_id}")

    points = point_repo.lister_par_zone(etude_id)
    repetitions = []
    sonde_ids = set()
    outil_ids = set()
    for point in points:
        for repetition in repetition_repo.lister_par_point(point.id):
            repetitions.append(repetition)
            if repetition.sonde_id is not None:
                sonde_ids.add(repetition.sonde_id)
            if repetition.outil_id is not None:
                outil_ids.add(repetition.outil_id)

    sondes = [sonde_repo.trouver_par_id(sonde_id) for sonde_id in sorted(sonde_ids)]
    outils = [outil_repo.trouver_par_id(outil_id) for outil_id in sorted(outil_ids)]
    sondes = [sonde for sonde in sondes if sonde is not None]
    outils = [outil for outil in outils if outil is not None]

    study = {
        "zone": _zone_dict(zone),
        "points": [_point_dict(point) for point in points],
        "repetitions": [_repetition_dict(rep) for rep in repetitions],
        "sondes": [_sonde_dict(sonde) for sonde in sondes],
        "outils": [_outil_dict(outil) for outil in outils],
    }
    manifest = {
        "format": "HydroK",
        "format_version": 1,
        "app_version": APPLICATION_VERSION,
        "date_export": datetime.now(timezone.utc).isoformat(),
    }

    chemin = Path(destination)
    if chemin.suffix.lower() != ".hydrok":
        chemin = chemin.with_suffix(".hydrok")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(chemin, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        archive.writestr(
            "study.json",
            json.dumps(study, ensure_ascii=False, indent=2),
        )
    return chemin
