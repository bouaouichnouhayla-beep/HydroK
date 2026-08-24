from dataclasses import dataclass
from typing import Optional

@dataclass
class Sonde:
    nom: str
    longueur_totale:float
    diametre_interieur: float
    longueur_crepine: float
    id: Optional[int] = None