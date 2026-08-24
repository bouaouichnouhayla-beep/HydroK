"""Formatage des valeurs affichées dans le rapport PDF."""

from xml.sax.saxutils import escape

from reportlab.platypus import Paragraph


class PdfFormattingMixin:

    def _paragraphe(self, valeur, style="cellule"):
        if isinstance(valeur, Paragraph):
            return valeur
        texte = "" if valeur is None else escape(str(valeur))
        return Paragraph(texte, self.styles[style])

    @staticmethod
    def _format_decimal(valeur, decimales, fixe=False):
        """Formate un nombre avec une virgule sans exposer le flottant brut."""
        if valeur is None:
            return ""
        texte = f"{float(valeur):.{decimales}f}"
        if not fixe:
            texte = texte.rstrip("0").rstrip(".")
        return texte.replace(".", ",")

    @classmethod
    def _format_profondeur_cm(cls, valeur):
        if valeur is None:
            return ""
        profondeur = float(valeur) * 100
        if abs(profondeur - round(profondeur)) < 1e-9:
            return str(round(profondeur))
        return cls._format_decimal(profondeur, 2)

    @staticmethod
    def _format_k_markup(valeur):
        if valeur is None:
            return ""
        mantisse, exposant = f"{float(valeur):.3e}".split("e")
        mantisse = mantisse.replace(".", ",")
        return f"{mantisse} × 10<super>{int(exposant)}</super>"

    def _format_k_pdf(self, valeur, style="cellule", avec_unite=False):
        texte = self._format_k_markup(valeur)
        if texte and avec_unite:
            texte += " m/s"
        return Paragraph(texte, self.styles[style])

    @staticmethod
    def _format_valeur_technique(valeur):
        if valeur is None:
            return ""
        texte = str(valeur).strip().lower()
        libelles = {
            "en_cours": "En cours",
            "terminee": "Terminée",
            "terminée": "Terminée",
            "brouillon": "Brouillon",
        }
        return libelles.get(texte, texte.replace("_", " ").capitalize())

    @staticmethod
    def _enumeration(elements):
        if not elements:
            return ""
        if len(elements) == 1:
            return elements[0]
        return ", ".join(elements[:-1]) + " et " + elements[-1]

    @staticmethod
    def _parametres_materiel(ligne):
        if ligne.categorie == "sonde":
            parametres = (
                ("Longueur totale", ligne.longueur_totale, "m"),
                ("Diamètre intérieur", ligne.diametre_interieur, "m"),
                ("Longueur de crépine", ligne.longueur_crepine, "m"),
                ("Facteur C", ligne.facteur_c, ""),
            )
        elif ligne.type_materiel == "tuyau":
            parametres = (
                ("Diamètre", ligne.diametre_interieur, "m"),
                ("Hauteur", ligne.hauteur, "m"),
            )
        else:
            parametres = tuple(
                (nom, getattr(ligne, nom), "m")
                for nom in ("L1", "L2", "D1", "D2", "D3")
            )
        return " · ".join(
            f"{nom} : {PdfFormattingMixin._format_decimal(valeur, 3, fixe=True)}"
            f"{' ' + unite if unite else ''}"
            for nom, valeur, unite in parametres
            if valeur is not None
        )
