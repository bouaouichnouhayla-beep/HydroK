from dataclasses import dataclass
from typing import Optional

@dataclass
class Repetition:
    point_id: int
    sonde_id: int
    outil_id: int
    methode: str

    profondeur_enfoncement: float
    hauteur_eau: float
    hauteur_air: float
    temps_infiltration: float

    volume_eau: Optional[float] = None

    h_debut: Optional[float] = None
    h_fin: Optional[float] = None

    k_calcule: Optional[float] = None
    est_aberrante: bool = False

    commentaire: Optional[str] = None
    id: Optional[int] = None