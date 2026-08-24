"""Prépare les tableaux détaillés des synthèses et des futurs exports."""

from dataclasses import dataclass
from typing import Optional

from repositories.outil_repository import OutilRepository
from repositories.point_repository import PointRepository
from repositories.repetition_repository import RepetitionRepository
from repositories.sonde_repository import SondeRepository
from repositories.zone_repository import ZoneRepository


@dataclass(frozen=True)
class LigneRepetitionSynthese:
    repetition_id: int
    nom_etude: str
    nom_point: str
    latitude: Optional[float]
    longitude: Optional[float]
    facies: Optional[str]
    numero_repetition: int
    date: Optional[str]
    heure: Optional[str]
    profondeur_enfoncement: Optional[float]
    hauteur_eau: Optional[float]
    hauteur_air: Optional[float]
    volume_eau: Optional[float]
    h_debut: Optional[float]
    h_fin: Optional[float]
    temps_infiltration: Optional[float]
    methode: Optional[str]
    nom_outil: Optional[str]
    nom_sonde: Optional[str]
    k_calcule: Optional[float]
    commentaire: Optional[str]


@dataclass(frozen=True)
class LigneMaterielSynthese:
    materiel_id: int
    nom: str
    categorie: str
    type_materiel: Optional[str] = None
    diametre_interieur: Optional[float] = None
    hauteur: Optional[float] = None
    L1: Optional[float] = None
    L2: Optional[float] = None
    D1: Optional[float] = None
    D2: Optional[float] = None
    D3: Optional[float] = None
    longueur_totale: Optional[float] = None
    longueur_crepine: Optional[float] = None
    facteur_c: Optional[float] = None


@dataclass(frozen=True)
class DonneesTableauxSynthese:
    repetitions: list[LigneRepetitionSynthese]
    materiels: list[LigneMaterielSynthese]


class SyntheseTableService:
    """Assemble les données des tableaux sans dépendre de Tkinter."""

    def __init__(self):
        self.zone_repo = ZoneRepository()
        self.point_repo = PointRepository()
        self.repetition_repo = RepetitionRepository()
        self.outil_repo = OutilRepository()
        self.sonde_repo = SondeRepository()

    def pour_point(self, point_id: int) -> DonneesTableauxSynthese:
        point = self.point_repo.trouver_par_id(point_id)
        if point is None:
            return DonneesTableauxSynthese([], [])

        zone = self.zone_repo.trouver_par_id(point.zone_id)
        return self._construire(zone, [point])

    def pour_zone(self, zone_id: int) -> DonneesTableauxSynthese:
        zone = self.zone_repo.trouver_par_id(zone_id)
        points = self.point_repo.lister_par_zone(zone_id)
        return self._construire(zone, points)

    def _construire(self, zone, points) -> DonneesTableauxSynthese:
        outils = {outil.id: outil for outil in self.outil_repo.lister()}
        sondes = {sonde.id: sonde for sonde in self.sonde_repo.lister()}
        lignes_repetitions = []
        materiels_utilises = []
        materiels_ajoutes = set()

        for point in points:
            repetitions = sorted(
                self.repetition_repo.lister_par_point(point.id),
                key=lambda repetition: repetition.id or 0,
            )
            for numero, repetition in enumerate(repetitions, start=1):
                outil = outils.get(repetition.outil_id)
                sonde = sondes.get(repetition.sonde_id)
                lignes_repetitions.append(LigneRepetitionSynthese(
                    repetition_id=repetition.id,
                    nom_etude=zone.nom if zone else "",
                    nom_point=point.nom,
                    latitude=point.latitude,
                    longitude=point.longitude,
                    facies=point.facies,
                    numero_repetition=numero,
                    date=zone.date_campagne if zone else None,
                    heure=None,
                    profondeur_enfoncement=repetition.profondeur_enfoncement,
                    hauteur_eau=repetition.hauteur_eau,
                    hauteur_air=repetition.hauteur_air,
                    volume_eau=repetition.volume_eau,
                    h_debut=repetition.h_debut,
                    h_fin=repetition.h_fin,
                    temps_infiltration=repetition.temps_infiltration,
                    methode=repetition.methode,
                    nom_outil=outil.nom if outil else None,
                    nom_sonde=sonde.nom if sonde else None,
                    k_calcule=repetition.k_calcule,
                    commentaire=repetition.commentaire,
                ))

                self._ajouter_outil(
                    outil, materiels_utilises, materiels_ajoutes
                )
                self._ajouter_sonde(
                    sonde, materiels_utilises, materiels_ajoutes
                )

        return DonneesTableauxSynthese(
            lignes_repetitions, materiels_utilises
        )

    @staticmethod
    def _ajouter_outil(outil, lignes, materiels_ajoutes):
        if outil is None or ("outil", outil.id) in materiels_ajoutes:
            return

        materiels_ajoutes.add(("outil", outil.id))
        if outil.type_outil == "tuyau":
            lignes.append(LigneMaterielSynthese(
                materiel_id=outil.id,
                nom=outil.nom,
                categorie="outil",
                type_materiel="tuyau",
                diametre_interieur=outil.diametre_interieur,
                hauteur=outil.hauteur_tuyau,
            ))
        else:
            lignes.append(LigneMaterielSynthese(
                materiel_id=outil.id,
                nom=outil.nom,
                categorie="outil",
                type_materiel="entonnoir",
                L1=outil.L1,
                L2=outil.L2,
                D1=outil.D1,
                D2=outil.D2,
                D3=outil.D3,
            ))

    @staticmethod
    def _ajouter_sonde(sonde, lignes, materiels_ajoutes):
        if sonde is None or ("sonde", sonde.id) in materiels_ajoutes:
            return

        materiels_ajoutes.add(("sonde", sonde.id))
        lignes.append(LigneMaterielSynthese(
            materiel_id=sonde.id,
            nom=sonde.nom,
            categorie="sonde",
            diametre_interieur=sonde.diametre_interieur,
            longueur_totale=sonde.longueur_totale,
            longueur_crepine=sonde.longueur_crepine,
            facteur_c=None,
        ))
