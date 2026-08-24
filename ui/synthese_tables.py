"""Tableaux communs aux synthèses d'un point et d'une étude."""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from ui import theme
from ui.widgets import Card, configurer_zebrage, inserer_ligne


def _texte(valeur):
    return "—" if valeur is None or valeur == "" else valeur


def afficher_repetitions(
    parent, lignes, afficher_point=False, aberrantes_ids=None
):
    """Affiche une ligne par répétition à partir des données préparées."""
    card = Card(parent, padding=0)
    card.pack(fill="x", pady=(8, 24))

    colonnes = [
        ("etude", "Étude", 130),
        ("latitude", "Latitude", 90),
        ("longitude", "Longitude", 90),
        ("facies", "Faciès", 100),
        ("numero", "Rép.", 55),
        ("date", "Date campagne", 105),
        ("profondeur", "h_p (cm)", 80),
        ("hw", "h_w (cm)", 80),
        ("ha", "h_a (cm)", 80),
        ("volume", "Volume (L)", 85),
        ("h_debut", "h début (cm)", 90),
        ("h_fin", "h fin (cm)", 85),
        ("temps", "Temps (s)", 80),
        ("methode", "Méthode", 90),
        ("outil", "Outil", 130),
        ("sonde", "Sonde", 130),
        ("k", "K (m/s)", 125),
        ("commentaire", "Commentaire", 180),
    ]
    if afficher_point:
        colonnes.insert(1, ("point", "Point", 110))
    if aberrantes_ids is not None:
        colonnes.append(("statut", "Statut", 85))

    cles = [colonne[0] for colonne in colonnes]
    table = ttk.Treeview(
        card.corps, columns=cles, show="headings",
        height=min(max(len(lignes), 1), 12),
    )
    configurer_zebrage(table)
    for cle, libelle, largeur in colonnes:
        table.heading(cle, text=libelle)
        table.column(
            cle, width=largeur, minwidth=largeur,
            anchor="center", stretch=False,
        )

    for index, ligne in enumerate(lignes):
        valeurs = {
            "etude": _texte(ligne.nom_etude),
            "point": _texte(ligne.nom_point),
            "latitude": _texte(ligne.latitude),
            "longitude": _texte(ligne.longitude),
            "facies": _texte(ligne.facies),
            "numero": ligne.numero_repetition,
            "date": _texte(ligne.date),
            "profondeur": theme.format_cm(ligne.profondeur_enfoncement),
            "hw": theme.format_cm(ligne.hauteur_eau),
            "ha": theme.format_cm(ligne.hauteur_air),
            "volume": _texte(ligne.volume_eau),
            "h_debut": theme.format_cm(ligne.h_debut),
            "h_fin": theme.format_cm(ligne.h_fin),
            "temps": _texte(ligne.temps_infiltration),
            "methode": _texte(ligne.methode),
            "outil": _texte(ligne.nom_outil),
            "sonde": _texte(ligne.nom_sonde),
            "k": theme.format_k(ligne.k_calcule),
            "commentaire": _texte(ligne.commentaire),
            "statut": (
                "⚠ Aberrante"
                if aberrantes_ids is not None
                and ligne.repetition_id in aberrantes_ids
                else "OK"
            ),
        }
        inserer_ligne(
            table, index, str(ligne.repetition_id),
            tuple(valeurs[cle] for cle in cles),
            aberrante=(aberrantes_ids is not None
                       and ligne.repetition_id in aberrantes_ids),
        )

    _installer_defilement(card, table)
    return table


def afficher_materiels(parent, lignes):
    """Affiche une seule ligne par matériel effectivement utilisé."""
    card = Card(parent, padding=0)
    card.pack(fill="x", pady=(8, 24))

    colonnes = [
        ("nom", "Référence / nom", 150),
        ("categorie", "Catégorie", 80),
        ("type", "Type", 90),
        ("diametre", "Ø intérieur (cm)", 105),
        ("hauteur", "Hauteur (cm)", 95),
        ("L1", "L1 (cm)", 75),
        ("L2", "L2 (cm)", 75),
        ("D1", "D1 (cm)", 75),
        ("D2", "D2 (cm)", 75),
        ("D3", "D3 (cm)", 75),
        ("longueur_totale", "Long. totale (cm)", 115),
        ("longueur_crepine", "Crépine (cm)", 95),
        ("facteur_c", "Facteur C", 90),
    ]
    cles = [colonne[0] for colonne in colonnes]
    table = ttk.Treeview(
        card.corps, columns=cles, show="headings",
        height=min(max(len(lignes), 1), 10),
    )
    configurer_zebrage(table)
    for cle, libelle, largeur in colonnes:
        table.heading(cle, text=libelle)
        table.column(
            cle, width=largeur, minwidth=largeur,
            anchor="center", stretch=False,
        )

    for index, ligne in enumerate(lignes):
        valeurs = (
            ligne.nom,
            ligne.categorie,
            _texte(ligne.type_materiel),
            theme.format_cm(ligne.diametre_interieur),
            theme.format_cm(ligne.hauteur),
            theme.format_cm(ligne.L1),
            theme.format_cm(ligne.L2),
            theme.format_cm(ligne.D1),
            theme.format_cm(ligne.D2),
            theme.format_cm(ligne.D3),
            theme.format_cm(ligne.longueur_totale),
            theme.format_cm(ligne.longueur_crepine),
            _texte(ligne.facteur_c),
        )
        inserer_ligne(table, index, str(index), valeurs)

    _installer_defilement(card, table)
    return table


def afficher_materiels_etude(parent, lignes):
    """Sépare les outils et les sondes utilisés dans l'étude."""
    largeur_min_cote_a_cote = 1180
    outils = _materiels_uniques(lignes, "outil")
    sondes = _materiels_uniques(lignes, "sonde")

    conteneur = tk.Frame(parent, bg=theme.BG)
    conteneur.pack(fill="x", pady=(8, 24))

    carte_outils = Card(conteneur, titre="Outils utilisés", padding=14)
    carte_sondes = Card(conteneur, titre="Sondes utilisées", padding=14)

    colonnes_outils = [
        ("nom", "Référence / nom", 125),
        ("type", "Type", 70),
        ("parametres", "Paramètres", 180),
    ]
    valeurs_outils = [
        (
            ligne.nom,
            _texte(ligne.type_materiel).capitalize(),
            _parametres_outil(ligne),
        )
        for ligne in outils
    ]
    _creer_table_materiel(
        carte_outils,
        colonnes_outils,
        valeurs_outils,
        colonne_flexible="parametres",
    )

    colonnes_sondes = [
        ("nom", "Référence / nom", 160),
        ("longueur_totale", "Longueur totale (cm)", 130),
        ("longueur_crepine", "Longueur de crépine (cm)", 150),
    ]
    if any(ligne.facteur_c is not None for ligne in sondes):
        colonnes_sondes.append(("facteur_c", "Facteur C", 90))

    valeurs_sondes = []
    for ligne in sondes:
        valeurs = [
            ligne.nom,
            theme.format_cm(ligne.longueur_totale),
            theme.format_cm(ligne.longueur_crepine),
        ]
        if len(colonnes_sondes) == 4:
            valeurs.append(_texte(ligne.facteur_c))
        valeurs_sondes.append(tuple(valeurs))
    _creer_table_materiel(carte_sondes, colonnes_sondes, valeurs_sondes)

    disposition = {"large": None}

    def adapter_disposition(event):
        large = event.width >= largeur_min_cote_a_cote
        if disposition["large"] == large:
            return
        disposition["large"] = large
        carte_outils.grid_forget()
        carte_sondes.grid_forget()
        if large:
            conteneur.columnconfigure(0, weight=1, uniform="materiel")
            conteneur.columnconfigure(1, weight=1, uniform="materiel")
            carte_outils.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
            carte_sondes.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        else:
            conteneur.columnconfigure(0, weight=1, uniform="")
            conteneur.columnconfigure(1, weight=0, uniform="")
            carte_outils.grid(row=0, column=0, sticky="ew", pady=(0, 12))
            carte_sondes.grid(row=1, column=0, sticky="ew")

    conteneur.bind("<Configure>", adapter_disposition)
    return conteneur


def _materiels_uniques(lignes, categorie):
    uniques = {}
    for ligne in lignes:
        if ligne.categorie == categorie:
            uniques.setdefault(ligne.materiel_id, ligne)
    return list(uniques.values())


def _parametres_outil(ligne):
    if ligne.type_materiel == "tuyau":
        parametres = (
            ("Ø intérieur", ligne.diametre_interieur),
            ("hauteur", ligne.hauteur),
        )
    else:
        parametres = (
            ("L1", ligne.L1),
            ("L2", ligne.L2),
            ("D1", ligne.D1),
            ("D2", ligne.D2),
            ("D3", ligne.D3),
        )
    return "  ·  ".join(
        f"{nom} : {theme.format_cm(valeur)} cm"
        for nom, valeur in parametres
    )


def _creer_table_materiel(
    card, colonnes, valeurs, colonne_flexible=None
):
    cles = [colonne[0] for colonne in colonnes]
    table = ttk.Treeview(
        card.corps,
        columns=cles,
        show="headings",
        height=min(max(len(valeurs), 1), 8),
    )
    configurer_zebrage(table)
    police_cellule = tkfont.Font(font=theme.f_body(10))
    police_entete = tkfont.Font(font=theme.f_label(9))
    minimums = {}
    for index, (cle, libelle, largeur) in enumerate(colonnes):
        largeur_contenu = max(
            (police_cellule.measure(str(ligne[index])) for ligne in valeurs),
            default=0,
        )
        largeur_minimale = max(
            largeur,
            police_entete.measure(libelle) + 24,
            largeur_contenu + 24,
        )
        minimums[cle] = largeur_minimale
        table.heading(cle, text=libelle)
        table.column(
            cle,
            width=largeur_minimale,
            minwidth=largeur_minimale,
            anchor="center",
            stretch=False,
        )
    for index, ligne in enumerate(valeurs):
        inserer_ligne(table, index, str(index), ligne)
    actualiser_barre_h = _installer_defilement(
        card, table, barre_h_auto=True
    )

    total_minimum = sum(minimums.values())

    def ajuster_colonnes(event):
        # Réserve la bordure interne du Treeview pour éviter un débordement.
        largeur_disponible = max(1, event.width - 6)
        if largeur_disponible < total_minimum:
            largeurs = minimums
        elif colonne_flexible is not None:
            largeurs = minimums.copy()
            largeurs[colonne_flexible] += largeur_disponible - total_minimum
        else:
            surplus = largeur_disponible - total_minimum
            largeurs = minimums.copy()
            quotient, reste = divmod(surplus, len(colonnes))
            for index, (cle, _, _) in enumerate(colonnes):
                largeurs[cle] += quotient + (1 if index < reste else 0)

        for cle, _, _ in colonnes:
            table.column(cle, width=largeurs[cle])
        table.after_idle(actualiser_barre_h)

    table.bind("<Configure>", ajuster_colonnes, add="+")
    return table


def _installer_defilement(card, table, barre_h_auto=False):
    barre_v = ttk.Scrollbar(card.corps, orient="vertical", command=table.yview)
    barre_h = ttk.Scrollbar(card.corps, orient="horizontal", command=table.xview)

    def actualiser_barre_h(premier=None, dernier=None):
        if premier is not None and dernier is not None:
            barre_h.set(premier, dernier)
        premier_reel, dernier_reel = table.xview()
        barre_h.set(premier_reel, dernier_reel)
        if premier_reel <= 0 and dernier_reel >= 1:
            barre_h.grid_remove()
        else:
            barre_h.grid()

    table.configure(
        yscrollcommand=barre_v.set,
        xscrollcommand=actualiser_barre_h if barre_h_auto else barre_h.set,
    )

    card.corps.columnconfigure(0, weight=1)
    card.corps.rowconfigure(0, weight=1)
    table.grid(row=0, column=0, sticky="nsew", padx=(14, 0), pady=(0, 0))
    barre_v.grid(row=0, column=1, sticky="ns", padx=(0, 6))
    barre_h.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
    if barre_h_auto:
        barre_h.grid_remove()
    return actualiser_barre_h
