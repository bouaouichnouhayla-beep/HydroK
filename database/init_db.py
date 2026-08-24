from contextlib import closing
from datetime import datetime
from pathlib import Path

from database.connection import DB_PATH, get_connection
from utils.logging_config import obtenir_logger

logger = obtenir_logger(__name__)


def _creer_tables(connexion):
    """Crée le schéma courant lorsque la base est neuve."""
    connexion.executescript("""
    CREATE TABLE IF NOT EXISTS zone (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        site TEXT,
        localisation TEXT,
        date_campagne TEXT,
        operateur TEXT,
        etat TEXT DEFAULT 'En cours',
        remarques TEXT
    );

    CREATE TABLE IF NOT EXISTS point_mesure (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_id INTEGER NOT NULL,
        nom TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        facies TEXT,
        commentaires TEXT,
        FOREIGN KEY (zone_id) REFERENCES zone(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS sonde (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        longueur_totale REAL,
        diametre_interieur REAL,
        longueur_crepine REAL
    );

    CREATE TABLE IF NOT EXISTS outil (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        type_outil TEXT NOT NULL,
        L1 REAL,
        L2 REAL,
        D1 REAL,
        D2 REAL,
        D3 REAL,
        diametre_interieur REAL,
        hauteur_tuyau REAL
    );

    CREATE TABLE IF NOT EXISTS repetition (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        point_id INTEGER NOT NULL,
        sonde_id INTEGER,
        outil_id INTEGER,
        methode TEXT NOT NULL,
        profondeur_enfoncement REAL,
        hauteur_eau REAL,
        hauteur_air REAL,
        temps_infiltration REAL,
        volume_eau REAL,
        h_debut REAL,
        h_fin REAL,
        k_calcule REAL,
        commentaire TEXT,
        FOREIGN KEY (point_id) REFERENCES point_mesure(id) ON DELETE CASCADE,
        FOREIGN KEY (sonde_id) REFERENCES sonde(id) ON DELETE SET NULL,
        FOREIGN KEY (outil_id) REFERENCES outil(id) ON DELETE SET NULL
    );
    """)


def _cles_etrangeres(connexion, table):
    return {
        ligne[3]: (ligne[2], ligne[4], ligne[6].upper())
        for ligne in connexion.execute(f"PRAGMA foreign_key_list({table})")
    }


def _migration_necessaire(connexion):
    return (
        _cles_etrangeres(connexion, "point_mesure")
        != {"zone_id": ("zone", "id", "CASCADE")}
        or _cles_etrangeres(connexion, "repetition")
        != {
            "point_id": ("point_mesure", "id", "CASCADE"),
            "sonde_id": ("sonde", "id", "SET NULL"),
            "outil_id": ("outil", "id", "SET NULL"),
        }
    )


def _chemin_sauvegarde(db_path):
    sauvegarde = db_path.with_name("conductivite_backup_avant_migration.db")
    if not sauvegarde.exists():
        return sauvegarde
    suffixe = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return db_path.with_name(
        f"conductivite_backup_avant_migration_{suffixe}.db"
    )


def _sauvegarder_base(db_path):
    sauvegarde = _chemin_sauvegarde(db_path)
    with closing(get_connection(db_path)) as source:
        with closing(get_connection(sauvegarde)) as destination:
            source.backup(destination)
    return sauvegarde


def migrer_contraintes(db_path=DB_PATH):
    """Migre les suppressions relationnelles sans altérer les identifiants."""
    db_path = Path(db_path)
    with closing(get_connection(db_path)) as connexion:
        if not _migration_necessaire(connexion):
            return None

    sauvegarde = _sauvegarder_base(db_path)
    with closing(get_connection(db_path)) as connexion:
        connexion.execute("PRAGMA foreign_keys = OFF")
        try:
            connexion.execute("BEGIN IMMEDIATE")
            instructions = (
                """CREATE TABLE point_mesure_migration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_id INTEGER NOT NULL,
                    nom TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    facies TEXT,
                    commentaires TEXT,
                    FOREIGN KEY (zone_id) REFERENCES zone(id)
                        ON DELETE CASCADE
                )""",
                """INSERT INTO point_mesure_migration
                SELECT id, zone_id, nom, latitude, longitude, facies,
                       commentaires
                FROM point_mesure""",
                """CREATE TABLE repetition_migration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    point_id INTEGER NOT NULL,
                    sonde_id INTEGER,
                    outil_id INTEGER,
                    methode TEXT NOT NULL,
                    profondeur_enfoncement REAL,
                    hauteur_eau REAL,
                    hauteur_air REAL,
                    temps_infiltration REAL,
                    volume_eau REAL,
                    h_debut REAL,
                    h_fin REAL,
                    k_calcule REAL,
                    commentaire TEXT,
                    FOREIGN KEY (point_id)
                        REFERENCES point_mesure_migration(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (sonde_id) REFERENCES sonde(id)
                        ON DELETE SET NULL,
                    FOREIGN KEY (outil_id) REFERENCES outil(id)
                        ON DELETE SET NULL
                )""",
                """INSERT INTO repetition_migration
                SELECT id, point_id, sonde_id, outil_id, methode,
                       profondeur_enfoncement, hauteur_eau, hauteur_air,
                       temps_infiltration, volume_eau, h_debut, h_fin,
                       k_calcule, commentaire
                FROM repetition""",
                "DROP TABLE repetition",
                "DROP TABLE point_mesure",
                "ALTER TABLE point_mesure_migration RENAME TO point_mesure",
                "ALTER TABLE repetition_migration RENAME TO repetition",
            )
            for instruction in instructions:
                connexion.execute(instruction)
            violations = connexion.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()
            if violations:
                raise RuntimeError(
                    "Migration annulée : des clés étrangères orphelines "
                    f"ont été détectées : {violations}"
                )
            connexion.commit()
        except Exception:
            connexion.rollback()
            raise
        finally:
            connexion.execute("PRAGMA foreign_keys = ON")
    return sauvegarde


def creer_base(db_path=DB_PATH):
    """Crée le schéma puis applique, si nécessaire, sa migration sûre."""
    db_path = Path(db_path)
    with closing(get_connection(db_path)) as connexion, connexion:
        _creer_tables(connexion)
    sauvegarde = migrer_contraintes(db_path)
    logger.info("Base SQLite prête : %s", db_path)
    if sauvegarde:
        logger.info("Sauvegarde créée avant migration : %s", sauvegarde)
    return sauvegarde


if __name__ == "__main__":
    creer_base()
