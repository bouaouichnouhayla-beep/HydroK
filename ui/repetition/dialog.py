"""Orchestration du dialogue de saisie d'une répétition."""

from repositories.outil_repository import OutilRepository
from repositories.repetition_repository import RepetitionRepository
from repositories.sonde_repository import SondeRepository
from ui.repetition.actions import RepetitionActionsMixin
from ui.repetition.form import RepetitionFormMixin
from ui.repetition.schema import RepetitionSchemaMixin


class RepetitionDialog(
    RepetitionFormMixin,
    RepetitionActionsMixin,
    RepetitionSchemaMixin,
):

    def __init__(self, parent, point_id, refresh_callback=None, repetition=None):
        self.point_id = point_id
        self.refresh_callback = refresh_callback
        self.repetition = repetition
        self.repo = RepetitionRepository()
        self.k_calcule = getattr(repetition, "k_calcule", None) if repetition else None
        self._enregistrement_en_cours = False
        self._confirmation_after_id = None

        self.sonde_repo = SondeRepository()
        self.outil_repo = OutilRepository()
        self.sondes = self.sonde_repo.lister()
        self.outils = self.outil_repo.lister()

        self.sonde_map = {f"{s.nom} (Ø {s.diametre_interieur * 100:.1f} cm)": s
                          for s in self.sondes}
        self.outil_map = {f"{o.nom} [{o.type_outil}]": o
                          for o in self.outils}

        est_modif = repetition is not None
        titre_page = "Modifier la répétition" if est_modif else "Saisir une répétition"
        self._construire_interface(parent, est_modif, titre_page)
