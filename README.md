# HydroK

HydroK est une application de saisie et de synthèse de mesures de conductivité hydraulique. Elle nécessite Python 3.12 ou une version plus récente.

## Installation et lancement

Sous Linux, créez et activez l’environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Sous Windows, créez et activez l’environnement virtuel :

```bat
python -m venv .venv
.venv\Scripts\activate
```

Installez ensuite les dépendances :

```bash
python -m pip install -r requirements.txt
```

Vérifiez l’installation :

```bash
python scripts/check_installation.py
```

Lancez HydroK :

```bash
python main.py
```

Sous Debian ou Ubuntu, le paquet système `python3-tk` peut être nécessaire pour l’interface graphique : `sudo apt install python3-tk`.

La carte interactive des points utilise OpenStreetMap et nécessite une connexion internet pour charger les tuiles.

La base de données SQLite conductivite.db est créée automatiquement à la racine du projet lors du premier lancement de HydroK. Elle est ensuite utilisée pour stocker localement les zones, les points de mesure, les répétitions et le matériel enregistrés dans l’application.

Les journaux techniques sont enregistrés dans le dossier logs/.
