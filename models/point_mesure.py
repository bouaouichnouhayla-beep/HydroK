from dataclasses import dataclass
from typing import Optional

@dataclass
class PointMesure:
    zone_id: int
    nom: str
    facies: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commentaires: Optional[str] = None
    id: Optional[int] = None