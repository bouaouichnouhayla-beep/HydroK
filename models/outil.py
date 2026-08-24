from dataclasses import dataclass
from typing import Optional

@dataclass
class Outil:
    nom: str
    type_outil: str
    id: Optional[int] = None

@dataclass
class Entonnoir(Outil):
    L1: float = 0.0
    L2: float = 0.0
    D1: float = 0.0
    D2: float = 0.0
    D3: float = 0.0

    def __post_init__(self):
        self.type_outil = "entonnoir"

@dataclass
class Tuyau(Outil):
    diametre_interieur: float = 0.0
    hauteur_tuyau: float = 0.0

    def __post_init__(self):
        self.type_outil = "tuyau"