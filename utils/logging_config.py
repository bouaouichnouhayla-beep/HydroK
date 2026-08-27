"""Configuration de journalisation commune à HydroK."""

import logging
import os
import sys
from pathlib import Path


def _chemin_fichier_log() -> Path:
    if not sys.platform.startswith("linux"):
        local_appdata = os.environ.get("LOCALAPPDATA")
        racine_etat = (
            Path(local_appdata).expanduser()
            if local_appdata
            else Path.home()
        )
        return racine_etat / "HydroK" / "logs" / "hydrok.log"
    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    racine_etat = (
        Path(xdg_state_home).expanduser()
        if xdg_state_home
        else Path.home() / ".local" / "state"
    )
    return racine_etat / "HydroK" / "hydrok.log"


LOG_FILE = _chemin_fichier_log()
LOG_DIR = LOG_FILE.parent
_HANDLER_MARKER = "hydrok_file_handler"


def configurer_logging(log_file=LOG_FILE) -> logging.Logger:
    """Configure le journal applicatif sans empêcher le démarrage en cas d'échec."""
    logger = logging.getLogger("hydrok")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if any(getattr(handler, "name", None) == _HANDLER_MARKER
           for handler in logger.handlers):
        return logger

    try:
        chemin = Path(log_file)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(chemin, encoding="utf-8")
        handler.name = _HANDLER_MARKER
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        logger.addHandler(handler)
    except OSError:
        # La journalisation ne doit jamais rendre l'application inutilisable.
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
    return logger


def obtenir_logger(module: str) -> logging.Logger:
    """Retourne un logger enfant après initialisation idempotente."""
    configurer_logging()
    return logging.getLogger(f"hydrok.{module}")
