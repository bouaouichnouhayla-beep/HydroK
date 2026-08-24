"""Prépare un cache Matplotlib portable avant son import."""

import os
import tempfile
from pathlib import Path


def _dossier_ecrivable(dossier: Path) -> bool:
    """Vérifie le dossier sans supprimer ni remplacer un cache existant."""
    try:
        dossier.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dossier):
            return True
    except OSError:
        return False


def configurer_cache_matplotlib() -> Path:
    """Définit MPLCONFIGDIR seulement si aucun chemin explicite n'est fourni."""
    chemin_explicite = os.environ.get("MPLCONFIGDIR")
    if chemin_explicite:
        return Path(chemin_explicite)

    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        dossier_defaut = base / "matplotlib"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        dossier_defaut = base / "matplotlib"

    if _dossier_ecrivable(dossier_defaut):
        return dossier_defaut

    dossier_secours = Path(tempfile.gettempdir()) / "hydrok-matplotlib-cache"
    dossier_secours.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(dossier_secours)
    return dossier_secours
