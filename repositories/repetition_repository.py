"""Accès aux répétitions de mesure."""

from contextlib import closing

from database.connection import DB_PATH, get_connection
from models import Repetition


class RepetitionRepository:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def connecter(self):
        return get_connection(self.db_path)

    def ajouter(self, repetition: Repetition) -> int:
        with closing(self.connecter()) as connexion, connexion:
            curseur = connexion.execute("""
                INSERT INTO repetition(
                    point_id, sonde_id, outil_id, methode,
                    profondeur_enfoncement, hauteur_eau, hauteur_air,
                    temps_infiltration, volume_eau, h_debut, h_fin,
                    k_calcule, commentaire
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repetition.point_id, repetition.sonde_id,
                repetition.outil_id, repetition.methode,
                repetition.profondeur_enfoncement, repetition.hauteur_eau,
                repetition.hauteur_air, repetition.temps_infiltration,
                repetition.volume_eau, repetition.h_debut, repetition.h_fin,
                repetition.k_calcule, repetition.commentaire,
            ))
            return curseur.lastrowid

    @staticmethod
    def _vers_modele(ligne):
        return Repetition(
            id=ligne[0], point_id=ligne[1], sonde_id=ligne[2],
            outil_id=ligne[3], methode=ligne[4],
            profondeur_enfoncement=ligne[5], hauteur_eau=ligne[6],
            hauteur_air=ligne[7], temps_infiltration=ligne[8],
            volume_eau=ligne[9], h_debut=ligne[10], h_fin=ligne[11],
            k_calcule=ligne[12], commentaire=ligne[13],
        )

    def lister_par_point(self, point_id: int) -> list[Repetition]:
        with closing(self.connecter()) as connexion:
            lignes = connexion.execute("""
                SELECT id, point_id, sonde_id, outil_id, methode,
                       profondeur_enfoncement, hauteur_eau, hauteur_air,
                       temps_infiltration, volume_eau, h_debut, h_fin,
                       k_calcule, commentaire
                FROM repetition
                WHERE point_id = ?
            """, (point_id,)).fetchall()
        return [self._vers_modele(ligne) for ligne in lignes]

    def lister_par_zone(self, point_id: int) -> list[Repetition]:
        """Conserve l'API historique, qui reçoit en réalité un point."""
        return self.lister_par_point(point_id)

    def supprimer(self, repetition_id: int):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute(
                "DELETE FROM repetition WHERE id = ?", (repetition_id,)
            )

    def modifier(self, repetition: Repetition):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("""
                UPDATE repetition
                SET sonde_id = ?, outil_id = ?, methode = ?,
                    profondeur_enfoncement = ?, hauteur_eau = ?,
                    hauteur_air = ?, temps_infiltration = ?, volume_eau = ?,
                    h_debut = ?, h_fin = ?, k_calcule = ?, commentaire = ?
                WHERE id = ?
            """, (
                repetition.sonde_id, repetition.outil_id, repetition.methode,
                repetition.profondeur_enfoncement, repetition.hauteur_eau,
                repetition.hauteur_air, repetition.temps_infiltration,
                repetition.volume_eau, repetition.h_debut, repetition.h_fin,
                repetition.k_calcule, repetition.commentaire, repetition.id,
            ))

    def trouver_par_id(self, repetition_id: int):
        with closing(self.connecter()) as connexion:
            ligne = connexion.execute("""
                SELECT id, point_id, sonde_id, outil_id, methode,
                       profondeur_enfoncement, hauteur_eau, hauteur_air,
                       temps_infiltration, volume_eau, h_debut, h_fin,
                       k_calcule, commentaire
                FROM repetition
                WHERE id = ?
            """, (repetition_id,)).fetchone()
        return None if ligne is None else self._vers_modele(ligne)

    def compter_par_point(self, point_id):
        with closing(self.connecter()) as connexion:
            return connexion.execute("""
                SELECT COUNT(*) FROM repetition WHERE point_id = ?
            """, (point_id,)).fetchone()[0]

    def moyenne_k_par_point(self, point_id):
        with closing(self.connecter()) as connexion:
            return connexion.execute("""
                SELECT AVG(k_calcule)
                FROM repetition
                WHERE point_id = ? AND k_calcule IS NOT NULL
            """, (point_id,)).fetchone()[0]

    def profondeurs_par_point(self, point_id):
        with closing(self.connecter()) as connexion:
            lignes = connexion.execute("""
                SELECT DISTINCT profondeur_enfoncement
                FROM repetition
                WHERE point_id = ? AND profondeur_enfoncement IS NOT NULL
                ORDER BY profondeur_enfoncement
            """, (point_id,)).fetchall()
        return ", ".join(str(ligne[0]) for ligne in lignes)

    def compter_par_zone(self, zone_id):
        with closing(self.connecter()) as connexion:
            return connexion.execute("""
                SELECT COUNT(*)
                FROM repetition r
                JOIN point_mesure p ON r.point_id = p.id
                WHERE p.zone_id = ?
            """, (zone_id,)).fetchone()[0]

    def moyenne_k_par_zone(self, zone_id):
        with closing(self.connecter()) as connexion:
            return connexion.execute("""
                SELECT AVG(r.k_calcule)
                FROM repetition r
                JOIN point_mesure p ON r.point_id = p.id
                WHERE p.zone_id = ? AND r.k_calcule IS NOT NULL
            """, (zone_id,)).fetchone()[0]

    def profondeurs_par_zone(self, zone_id):
        with closing(self.connecter()) as connexion:
            lignes = connexion.execute("""
                SELECT DISTINCT profondeur_enfoncement
                FROM repetition r
                JOIN point_mesure p ON r.point_id = p.id
                WHERE p.zone_id = ?
                ORDER BY profondeur_enfoncement
            """, (zone_id,)).fetchall()
        return [ligne[0] for ligne in lignes]
