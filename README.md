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

## Installation de HydroK sous Linux

### Version distribuable

La version Linux prête à être installée est disponible dans :

HydroK-Linux.zip

### Installation sur une autre machine Linux

1. Copier `HydroK-Linux.zip` sur la machine Linux.

2. Décompresser l’archive.

3. Ouvrir le dossier `HydroK-Linux`.

4. Ouvrir un terminal dans ce dossier.

5. Exécuter :

chmod +x install_linux.sh
./install_linux.sh

6. Une fois l’installation terminée, ouvrir le menu des applications.

7. Rechercher `HydroK` puis lancer l’application.

### Prérequis

Python n’a pas besoin d’être installé séparément : la distribution contient
les composants nécessaires à l’exécution de HydroK.

### Connexion Internet

Une connexion Internet est nécessaire pour charger le fond de carte
OpenStreetMap.

Les autres fonctionnalités restent utilisables hors connexion selon leur
fonctionnement prévu.

### Données utilisateur

Les données de HydroK sont enregistrées dans les dossiers utilisateur Linux
et restent séparées des fichiers du programme.
