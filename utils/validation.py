"""Validations communes des valeurs saisies dans HydroK."""


def convertir_nombre(valeur, nom_champ="La valeur", obligatoire=False):
    """Convertit une saisie en nombre et produit une erreur fonctionnelle claire."""
    texte = "" if valeur is None else str(valeur).strip()
    if not texte:
        if obligatoire:
            raise ValueError(f"{nom_champ} est obligatoire.")
        return None
    try:
        return float(texte.replace(",", "."))
    except ValueError as erreur:
        raise ValueError(f"{nom_champ} doit être un nombre.") from erreur
