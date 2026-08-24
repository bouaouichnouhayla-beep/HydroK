"""Configuration de journalisation commune à HydroK."""

import logging
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "hydrok.log"
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
