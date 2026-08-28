"""Import atomique d'une étude HydroK au format ``.hydrok``."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from database.connection import DB_PATH, get_connection


class ImportEtudeError(ValueError):
    """Erreur de validation ou d'import d'un fichier HydroK."""


def _lire_export(fichier):
    chemin = Path(fichier)
    if not chemin.is_file():
        raise ImportEtudeError(f"Fichier .hydrok introuvable : {chemin}")
    try:
        with ZipFile(chemin) as archive:
            noms = set(archive.namelist())
            requis = {"manifest.json", "study.json"}
            if not requis.issubset(noms):
                manquants = ", ".join(sorted(requis - noms))
                raise ImportEtudeError(
                    f"Archive HydroK incomplète : {manquants} absent(s)"
                )
            try:
                manifest = json.loads(archive.read("manifest.json"))
                study = json.loads(archive.read("study.json"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ImportEtudeError(
                    "manifest.json ou study.json n'est pas un JSON UTF-8 valide"
                ) from exc
    except BadZipFile as exc:
        raise ImportEtudeError("Le fichier .hydrok n'est pas une archive ZIP valide") from exc

    if not isinstance(manifest, dict):
        raise ImportEtudeError("manifest.json doit contenir un objet JSON")
    if manifest.get("format") != "HydroK":
        raise ImportEtudeError("Format d'export inconnu (HydroK attendu)")
    if manifest.get("format_version") != 1:
        raise ImportEtudeError("Version de format non prise en charge")
    if not isinstance(study, dict):
        raise ImportEtudeError("study.json doit contenir un objet JSON")
    for cle in ("zone", "points", "repetitions", "sondes", "outils"):
        if cle not in study:
            raise ImportEtudeError(f"study.json incomplet : clé '{cle}' absente")
    if not isinstance(study["zone"], dict):
        raise ImportEtudeError("study.json.zone doit être un objet JSON")
    for cle in ("points", "repetitions", "sondes", "outils"):
        if not isinstance(study[cle], list):
            raise ImportEtudeError(f"study.json.{cle} doit être une liste")
    return study


def _nom_sans_conflit(connexion, nom):
    existants = {
        ligne[0]
        for ligne in connexion.execute("SELECT nom FROM zone").fetchall()
    }
    if nom not in existants:
        return nom
    base = f"{nom} (importée)"
    candidat = base
    compteur = 2
    while candidat in existants:
        candidat = f"{base} {compteur}"
        compteur += 1
    return candidat


def _exiger_champs(objet, champs, contexte):
    manquants = [champ for champ in champs if champ not in objet]
    if manquants:
        raise ImportEtudeError(
            f"{contexte} incomplet : {', '.join(manquants)} absent(s)"
        )


def import_etude(fichier, db_path=DB_PATH):
    """Recrée une étude dans ``db_path`` et renvoie son nouvel identifiant."""
    study = _lire_export(fichier)
    zone = study["zone"]
    _exiger_champs(
        zone,
        ("id", "nom", "site", "localisation", "date_campagne",
         "operateur", "etat", "remarques"),
        "zone",
    )

    chemin_base = Path(db_path)
    try:
        with closing(get_connection(chemin_base)) as connexion:
            connexion.execute("BEGIN")
            try:
                nom_zone = _nom_sans_conflit(connexion, zone["nom"])
                curseur = connexion.execute(
                    """INSERT INTO zone
                    (nom, site, localisation, date_campagne, operateur, etat, remarques)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (nom_zone, zone["site"], zone["localisation"],
                     zone["date_campagne"], zone["operateur"], zone["etat"],
                     zone["remarques"]),
                )
                nouveau_zone_id = curseur.lastrowid
                correspondances = {"zone": {zone["id"]: nouveau_zone_id},
                                   "point": {}, "sonde": {}, "outil": {}}

                for sonde in study["sondes"]:
                    _exiger_champs(
                        sonde,
                        ("id", "nom", "longueur_totale", "diametre_interieur",
                         "longueur_crepine"),
                        "sonde",
                    )
                    curseur = connexion.execute(
                        """INSERT INTO sonde
                        (nom, longueur_totale, diametre_interieur, longueur_crepine)
                        VALUES (?, ?, ?, ?)""",
                        (sonde["nom"], sonde["longueur_totale"],
                         sonde["diametre_interieur"], sonde["longueur_crepine"]),
                    )
                    correspondances["sonde"][sonde["id"]] = curseur.lastrowid

                for outil in study["outils"]:
                    _exiger_champs(
                        outil,
                        ("id", "nom", "type_outil", "L1", "L2", "D1", "D2",
                         "D3", "diametre_interieur", "hauteur_tuyau"),
                        "outil",
                    )
                    curseur = connexion.execute(
                        """INSERT INTO outil
                        (nom, type_outil, L1, L2, D1, D2, D3,
                         diametre_interieur, hauteur_tuyau)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (outil["nom"], outil["type_outil"], outil["L1"],
                         outil["L2"], outil["D1"], outil["D2"], outil["D3"],
                         outil["diametre_interieur"], outil["hauteur_tuyau"]),
                    )
                    correspondances["outil"][outil["id"]] = curseur.lastrowid

                for point in study["points"]:
                    _exiger_champs(
                        point,
                        ("id", "zone_id", "nom", "latitude", "longitude",
                         "facies", "commentaires"),
                        "point",
                    )
                    if point["zone_id"] != zone["id"]:
                        raise ImportEtudeError("Un point ne correspond pas à la zone exportée")
                    curseur = connexion.execute(
                        """INSERT INTO point_mesure
                        (zone_id, nom, latitude, longitude, facies, commentaires)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (nouveau_zone_id, point["nom"], point["latitude"],
                         point["longitude"], point["facies"], point["commentaires"]),
                    )
                    correspondances["point"][point["id"]] = curseur.lastrowid

                champs_repetition = (
                    "id", "point_id", "sonde_id", "outil_id", "methode",
                    "profondeur_enfoncement", "hauteur_eau", "hauteur_air",
                    "temps_infiltration", "volume_eau", "h_debut", "h_fin",
                    "k_calcule", "commentaire",
                )
                for repetition in study["repetitions"]:
                    _exiger_champs(repetition, champs_repetition, "répétition")
                    try:
                        point_id = correspondances["point"][repetition["point_id"]]
                    except KeyError as exc:
                        raise ImportEtudeError(
                            "Une répétition référence un point absent"
                        ) from exc
                    sonde_id = repetition["sonde_id"]
                    outil_id = repetition["outil_id"]
                    if sonde_id is not None and sonde_id not in correspondances["sonde"]:
                        raise ImportEtudeError("Une répétition référence une sonde absente")
                    if outil_id is not None and outil_id not in correspondances["outil"]:
                        raise ImportEtudeError("Une répétition référence un outil absent")
                    connexion.execute(
                        """INSERT INTO repetition
                        (point_id, sonde_id, outil_id, methode,
                         profondeur_enfoncement, hauteur_eau, hauteur_air,
                         temps_infiltration, volume_eau, h_debut, h_fin,
                         k_calcule, commentaire)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (point_id,
                         correspondances["sonde"].get(sonde_id),
                         correspondances["outil"].get(outil_id),
                         repetition["methode"], repetition["profondeur_enfoncement"],
                         repetition["hauteur_eau"], repetition["hauteur_air"],
                         repetition["temps_infiltration"], repetition["volume_eau"],
                         repetition["h_debut"], repetition["h_fin"],
                         repetition["k_calcule"], repetition["commentaire"]),
                    )
                connexion.commit()
                return nouveau_zone_id
            except Exception:
                connexion.rollback()
                raise
    except sqlite3.Error as exc:
        raise ImportEtudeError(f"Import SQLite impossible : {exc}") from exc
