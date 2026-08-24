"""Vérifie les prérequis Python de HydroK sans lancer l'application."""

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys


RACINE_PROJET = Path(__file__).resolve().parent.parent
if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from utils.matplotlib_config import configurer_cache_matplotlib


configurer_cache_matplotlib()

PYTHON_MINIMUM = (3, 12)
DEPENDANCES = {
    "numpy": "numpy",
    "sympy": "sympy",
    "matplotlib": "matplotlib",
    "Pillow": "PIL",
    "reportlab": "reportlab",
    "tkintermapview": "tkintermapview",
}


def main() -> int:
    erreurs = []
    version_python = ".".join(map(str, sys.version_info[:3]))
    print(f"Python {version_python}")
    if sys.version_info < PYTHON_MINIMUM:
        erreurs.append("Python 3.12 ou une version plus récente est nécessaire.")

    for distribution, module in DEPENDANCES.items():
        try:
            import_module(module)
            try:
                version_installee = version(distribution)
            except PackageNotFoundError:
                version_installee = "version inconnue"
            print(f"[OK] {distribution} {version_installee}")
        except ImportError as erreur:
            erreurs.append(f"Dépendance manquante : {distribution} ({erreur})")

    if erreurs:
        for erreur in erreurs:
            print(f"[ERREUR] {erreur}", file=sys.stderr)
        print(
            "Installez les dépendances avec : "
            "python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    print("Installation HydroK valide.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
