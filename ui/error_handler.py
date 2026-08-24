"""Messages d'erreur cohérents destinés aux utilisateurs de l'interface."""

import sqlite3
from tkinter import messagebox

from utils.logging_config import obtenir_logger


logger = obtenir_logger(__name__)


def afficher_erreur_saisie(message, parent=None):
    messagebox.showerror("Valeur invalide", message, parent=parent)


def afficher_erreur_enregistrement(parent=None):
    messagebox.showerror(
        "HydroK",
        "Cette opération n'a pas pu être enregistrée. Vérifiez les données saisies.",
        parent=parent,
    )


def afficher_erreur_export(parent=None, raison=None):
    messages = {
        "permission": "Permission insuffisante. Fermez le fichier s'il est ouvert, puis réessayez.",
        "dossier": "Le dossier de destination est inaccessible.",
    }
    messagebox.showerror(
        "HydroK", messages.get(raison, "L'export n'a pas pu être réalisé."),
        parent=parent,
    )


def afficher_erreur_inattendue(parent=None):
    messagebox.showerror(
        "HydroK", "Une erreur inattendue est survenue. Vous pouvez réessayer.",
        parent=parent,
    )


def traiter_erreur_sqlite(erreur, parent=None, contexte="opération SQLite"):
    """Journalise une erreur SQLite une seule fois et affiche un message fonctionnel."""
    if isinstance(erreur, sqlite3.IntegrityError):
        logger.warning("Échec d'intégrité pendant %s : %s", contexte, erreur)
    elif isinstance(erreur, sqlite3.OperationalError):
        logger.error("Échec opérationnel pendant %s", contexte, exc_info=True)
    else:
        logger.exception("Erreur de base de données pendant %s", contexte)
    afficher_erreur_enregistrement(parent)


def executer_callback_securise(callback, parent=None, contexte="action utilisateur"):
    """Limite extérieure d'un callback : empêche une exception de fermer l'interface."""
    try:
        return callback()
    except Exception:
        # Capture générale volontaire à la frontière Tkinter : le détail reste au journal.
        logger.exception("Erreur inattendue pendant %s", contexte)
        afficher_erreur_inattendue(parent)
        return None
