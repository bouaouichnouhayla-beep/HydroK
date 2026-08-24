from contextlib import closing

from database.connection import DB_PATH, get_connection
from models import Zone

class ZoneRepository:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
    
    def connecter(self):
        return get_connection(self.db_path)

    def ajouter(self, zone: Zone) -> int:
        with closing(self.connecter()) as connexion, connexion:
            curseur = connexion.execute("""
                INSERT INTO zone(
                    nom, site, localisation, date_campagne,
                    operateur, etat, remarques
                )
                VALUES(?, ?, ?, ?, ?, ?, ?)
            """, (
                zone.nom, zone.site, zone.localisation, zone.date_campagne,
                zone.operateur, zone.etat, zone.remarques
            ))
            return curseur.lastrowid
    
    def lister(self) -> list[Zone]:
        with closing(self.connecter()) as connexion:
            lignes = connexion.execute("""
                SELECT id, nom, site, localisation, date_campagne,
                       operateur, etat, remarques
                FROM zone
            """).fetchall()

        zones = []

        for ligne in lignes:
            zone = Zone(
                id=ligne[0],
                nom=ligne[1],
                site=ligne[2],
                localisation=ligne[3],
                date_campagne=ligne[4],
                operateur=ligne[5],
                etat=ligne[6],
                remarques=ligne[7]
            )
            zones.append(zone)

        return zones
    
    def trouver_par_id(self, zone_id: int) -> Zone | None:
        with closing(self.connecter()) as connexion:
            ligne = connexion.execute("""
                SELECT id, nom, site, localisation, date_campagne,
                       operateur, etat, remarques
                FROM zone
                WHERE id = ?
            """, (zone_id,)).fetchone()

        if ligne is None:
            return None
        
        return Zone(
            
                id=ligne[0],
                nom=ligne[1],
                site=ligne[2],
                localisation=ligne[3],
                date_campagne=ligne[4],
                operateur=ligne[5],
                etat=ligne[6],
                remarques=ligne[7]
            )
    def supprimer(self, zone_id: int):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("DELETE FROM zone WHERE id = ?", (zone_id,))

    def modifier(self, zone):
        with closing(self.connecter()) as connexion, connexion:
            connexion.execute("""
                UPDATE zone
                SET nom = ?, site = ?, date_campagne = ?, operateur = ?,
                    etat = ?, localisation = ?, remarques = ?
                WHERE id = ?
            """, (
                zone.nom, zone.site, zone.date_campagne, zone.operateur,
                zone.etat, zone.localisation, zone.remarques, zone.id
            ))
