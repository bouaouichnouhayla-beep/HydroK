"""
services/calcul_service.py
=================================================
Service de calcul de la conductivité hydraulique K.

Ce service est l'unique point d'entrée utilisé par l'interface
graphique (ui/repetition_dialog.py) pour calculer K. Il délègue
aux formules scientifiques de services/CalculerK.py, qui ne sont
PAS modifiées ici (seules des validations défensives ont été
ajoutées dans CalculerK.py pour éviter les calculs incohérents).

IMPORTANT — unités attendues : toutes les grandeurs passées à ce
service (et aux fonctions de CalculerK.py) sont en MÈTRES et en
SECONDES, conformément aux formules scientifiques d'origine. La
conversion centimètres -> mètres pour la saisie utilisateur est
effectuée en amont, dans ui/repetition_dialog.py, avant l'appel
à ce service.
=================================================
"""

from services.CalculerK import Datry, InfiltrationTuyau


class CalculService:

    def calculer_k_tuyau(self, ha, temps, diametre_tuyau, hauteur_tuyau,
                          h_debut, h_fin, longueur_crepine, diametre_sonde):
        """
        Calcule K avec la méthode TUYAU.
        La sonde (longueur_crepine, diametre_sonde) est obligatoire :
        elle conditionne directement le coefficient de forme C.
        """
        return InfiltrationTuyau(
            ha,
            temps,
            diametre_tuyau,
            hauteur_tuyau,
            h_debut,
            h_fin,
            longueur_crepine,
            diametre_sonde
        )

    def calculer_k_entonnoir(self, ha, temps, L1, L2, D1, D2, D3, volume_eau,
                              longueur_crepine=None, diametre_sonde=None):
        """
        Calcule K avec la méthode ENTONNOIR.
        La sonde (longueur_crepine, diametre_sonde) est optionnelle pour
        compatibilité ascendante : si elle n'est pas fournie, les valeurs
        historiques de la sonde "Tube HC18" sont utilisées par défaut.
        Il est cependant recommandé de toujours la transmettre pour que
        le calcul reflète fidèlement le matériel utilisé sur le terrain.
        """
        kwargs = {}
        if longueur_crepine is not None:
            kwargs["longueur_crepine"] = longueur_crepine
        if diametre_sonde is not None:
            kwargs["diametre_sonde"] = diametre_sonde

        k, h0 = Datry(
            ha,
            temps,
            L1,
            L2,
            D1,
            D2,
            D3,
            volume_eau,
            **kwargs
        )
        return k
