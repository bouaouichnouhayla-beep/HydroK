"""Gestion du schéma de méthode affiché dans le dialogue."""

from ui.repetition.constants import SCHEMAS_DIR


class RepetitionSchemaMixin:

    def _dessiner_schema(self, outil):
        """Affiche le schéma de la méthode sélectionnée."""
        if outil is None:
            self.schema_methode.afficher_message(
                "Sélectionnez un outil\npour afficher le schéma\nde la méthode."
            )
            return

        if outil.type_outil == "tuyau":
            chemin_image = SCHEMAS_DIR / "methode_tuyau.png"
            titre = "Méthode par tuyau"
        else:
            chemin_image = SCHEMAS_DIR / "methode_entonnoir.png"
            titre = "Méthode par entonnoir"
        self.schema_methode.afficher(chemin_image, titre)
