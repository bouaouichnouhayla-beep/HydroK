
from contextlib import closing

from database.connection import DB_PATH, get_connection
from models import PointMesure

class PointRepository:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def connecter(self):
        return get_connection(self.db_path)

    def ajouter(self, point: PointMesure) -> int:
        with closing(self.connecter()) as connexion, connexion:
            curseur = connexion.execute("""
            INSERT INTO point_mesure (
                zone_id,
                nom,
                latitude,
                longitude,
                facies,
                commentaires
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                point.zone_id, point.nom, point.latitude, point.longitude,
                point.facies, point.commentaires
            ))
            return curseur.lastrowid

    def lister_par_zone(self, zone_id: int):
        with closing(self.connecter()) as connexion:
            lignes = connexion.execute("""
                SELECT id, zone_id, nom, latitude, longitude, facies,
                       commentaires
                FROM point_mesure
                WHERE zone_id = ?
            """, (zone_id,)).fetchall()

        points = []

        for ligne in lignes:
            point = PointMesure(
                id=ligne[0],
                zone_id=ligne[1],
                nom=ligne[2],
                latitude=ligne[3],
                longitude=ligne[4],
                facies=ligne[5],
                commentaires=ligne[6]
            )
            points.append(point)

        return points
    
    def supprimer(self, point_id):

        with closing(self.connecter()) as connexion, connexion:
            connexion.execute(
                "DELETE FROM point_mesure WHERE id = ?", (point_id,)
            )

    def trouver_par_id(self, point_id: int):
        with closing(self.connecter()) as connexion:
            ligne = connexion.execute("""
                SELECT id, zone_id, nom, latitude, longitude, facies,
                       commentaires
                FROM point_mesure
                WHERE id = ?
            """, (point_id,)).fetchone()

        if ligne is None:
            return None

        return PointMesure(
            id=ligne[0],
            zone_id=ligne[1],
            nom=ligne[2],
            latitude=ligne[3],
            longitude=ligne[4],
            facies=ligne[5],
            commentaires=ligne[6]

    )

    def modifier(self, point):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("""
            UPDATE point_mesure
            SET nom = ?, facies = ?, latitude = ?, longitude = ?, commentaires = ?
            WHERE id = ?
            """, (
                point.nom, point.facies, point.latitude, point.longitude,
                point.commentaires, point.id
            ))

    
    def compter_par_zone(self, zone_id):
        with closing(self.connecter()) as connexion:
            return connexion.execute("""
                SELECT COUNT(*) FROM point_mesure WHERE zone_id = ?
            """, (zone_id,)).fetchone()[0]
