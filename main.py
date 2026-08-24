"""Point d'entrée de l'application HydroK."""

from database.init_db import creer_base
from ui.main_window import MainWindow
from utils.logging_config import obtenir_logger


logger = obtenir_logger(__name__)


def main():
    """Lance l'interface graphique."""
    try:
        creer_base()
        logger.info("Base de données initialisée")
        app = MainWindow()
        logger.info("Démarrage de l'interface HydroK")
        app.run()
    except Exception:
        # Dernière frontière de sécurité : conserve le traceback avant de quitter.
        logger.exception("Échec fatal au démarrage ou dans la boucle principale")
        raise


if __name__ == "__main__":
    main()
