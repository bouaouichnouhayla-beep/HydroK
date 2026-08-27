"""Connexion SQLite commune de l'application HydroK."""

import os
import sqlite3
import sys
from pathlib import Path


def _chemin_base_utilisateur() -> Path:
    if not sys.platform.startswith("linux"):
        local_appdata = os.environ.get("LOCALAPPDATA")
        racine_donnees = (
            Path(local_appdata).expanduser()
            if local_appdata
            else Path.home()
        )
        return racine_donnees / "HydroK" / "conductivite.db"
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    racine_donnees = (
        Path(xdg_data_home).expanduser()
        if xdg_data_home
        else Path.home() / ".local" / "share"
    )
    return racine_donnees / "HydroK" / "conductivite.db"


DB_PATH = _chemin_base_utilisateur()


def get_connection(db_path=DB_PATH) -> sqlite3.Connection:
    """Ouvre la base demandée avec les contraintes relationnelles actives."""
    chemin = Path(db_path)
    if chemin == DB_PATH:
        chemin.parent.mkdir(parents=True, exist_ok=True)
    connexion = sqlite3.connect(chemin)
    connexion.execute("PRAGMA foreign_keys = ON")
    return connexion
