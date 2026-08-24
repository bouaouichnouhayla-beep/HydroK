"""Connexion SQLite commune de l'application HydroK."""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "conductivite.db"


def get_connection(db_path=DB_PATH) -> sqlite3.Connection:
    """Ouvre la base demandée avec les contraintes relationnelles actives."""
    connexion = sqlite3.connect(Path(db_path))
    connexion.execute("PRAGMA foreign_keys = ON")
    return connexion
