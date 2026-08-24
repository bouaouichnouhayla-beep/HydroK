"""Accès aux outils de mesure."""

from contextlib import closing

from database.connection import DB_PATH, get_connection
from models import Entonnoir, Tuyau


class OutilRepository:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def connecter(self):
        return get_connection(self.db_path)

    def ajouter_entonnoir(self, entonnoir: Entonnoir) -> int:
        with closing(self.connecter()) as connexion, connexion:
            curseur = connexion.execute("""
                INSERT INTO outil (nom, type_outil, L1, L2, D1, D2, D3)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entonnoir.nom, "entonnoir", entonnoir.L1, entonnoir.L2,
                entonnoir.D1, entonnoir.D2, entonnoir.D3,
            ))
            return curseur.lastrowid

    def ajouter_tuyau(self, tuyau: Tuyau) -> int:
        with closing(self.connecter()) as connexion, connexion:
            curseur = connexion.execute("""
                INSERT INTO outil (
                    nom, type_outil, diametre_interieur, hauteur_tuyau
                )
                VALUES (?, ?, ?, ?)
            """, (
                tuyau.nom, "tuyau", tuyau.diametre_interieur,
                tuyau.hauteur_tuyau,
            ))
            return curseur.lastrowid

    def lister(self):
        with closing(self.connecter()) as connexion:
            lignes = connexion.execute("SELECT * FROM outil").fetchall()

        outils = []
        for ligne in lignes:
            if ligne[2] == "entonnoir":
                outil = Entonnoir(
                    id=ligne[0], nom=ligne[1], type_outil="entonnoir",
                    L1=ligne[3], L2=ligne[4], D1=ligne[5], D2=ligne[6],
                    D3=ligne[7],
                )
            else:
                outil = Tuyau(
                    id=ligne[0], nom=ligne[1], type_outil="tuyau",
                    diametre_interieur=ligne[8], hauteur_tuyau=ligne[9],
                )
            outils.append(outil)
        return outils

    def modifier_entonnoir(self, entonnoir: Entonnoir):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("""
                UPDATE outil
                SET nom = ?, type_outil = ?, L1 = ?, L2 = ?, D1 = ?,
                    D2 = ?, D3 = ?, diametre_interieur = NULL,
                    hauteur_tuyau = NULL
                WHERE id = ?
            """, (
                entonnoir.nom, "entonnoir", entonnoir.L1, entonnoir.L2,
                entonnoir.D1, entonnoir.D2, entonnoir.D3, entonnoir.id,
            ))

    def modifier_tuyau(self, tuyau: Tuyau):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("""
                UPDATE outil
                SET nom = ?, type_outil = ?, L1 = NULL, L2 = NULL,
                    D1 = NULL, D2 = NULL, D3 = NULL,
                    diametre_interieur = ?, hauteur_tuyau = ?
                WHERE id = ?
            """, (
                tuyau.nom, "tuyau", tuyau.diametre_interieur,
                tuyau.hauteur_tuyau, tuyau.id,
            ))

    def supprimer(self, outil_id: int):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("DELETE FROM outil WHERE id = ?", (outil_id,))

    def trouver_par_id(self, outil_id: int):
        return next(
            (outil for outil in self.lister() if outil.id == outil_id), None
        )
