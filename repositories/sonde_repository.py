"""Accès aux sondes de mesure."""

from contextlib import closing

from database.connection import DB_PATH, get_connection
from models import Sonde


class SondeRepository:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def connecter(self):
        return get_connection(self.db_path)

    def ajouter(self, sonde: Sonde) -> int:
        with closing(self.connecter()) as connexion, connexion:
            curseur = connexion.execute("""
                INSERT INTO sonde (
                    nom, longueur_totale, diametre_interieur,
                    longueur_crepine
                )
                VALUES (?, ?, ?, ?)
            """, (
                sonde.nom, sonde.longueur_totale,
                sonde.diametre_interieur, sonde.longueur_crepine,
            ))
            return curseur.lastrowid

    def lister(self) -> list[Sonde]:
        with closing(self.connecter()) as connexion:
            lignes = connexion.execute("""
                SELECT id, nom, longueur_totale, diametre_interieur,
                       longueur_crepine
                FROM sonde
            """).fetchall()
        return [self._vers_modele(ligne) for ligne in lignes]

    @staticmethod
    def _vers_modele(ligne):
        return Sonde(
            id=ligne[0], nom=ligne[1], longueur_totale=ligne[2],
            diametre_interieur=ligne[3], longueur_crepine=ligne[4],
        )

    def trouver_par_id(self, sonde_id: int) -> Sonde | None:
        with closing(self.connecter()) as connexion:
            ligne = connexion.execute("""
                SELECT id, nom, longueur_totale, diametre_interieur,
                       longueur_crepine
                FROM sonde
                WHERE id = ?
            """, (sonde_id,)).fetchone()
        return None if ligne is None else self._vers_modele(ligne)

    def modifier(self, sonde: Sonde):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("""
                UPDATE sonde
                SET nom = ?, longueur_totale = ?, diametre_interieur = ?,
                    longueur_crepine = ?
                WHERE id = ?
            """, (
                sonde.nom, sonde.longueur_totale,
                sonde.diametre_interieur, sonde.longueur_crepine, sonde.id,
            ))

    def supprimer(self, sonde_id: int):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("DELETE FROM sonde WHERE id = ?", (sonde_id,))
