from dataclasses import dataclass
from typing import Optional

@dataclass
class Zone:
    nom: str
    site: str
    date_campagne: str
    operateur: str
    etat: str = "En cours"
    localisation: Optional[str] = None
    remarques: Optional[str] = None
    id: Optional[int] = None