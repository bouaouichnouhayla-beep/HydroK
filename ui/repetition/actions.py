"""Événements, calcul et enregistrement du dialogue de répétition."""

import sqlite3
import tkinter as tk
from tkinter import messagebox

from models import Repetition
from services.calcul_service import CalculService
from ui import theme
from ui.error_handler import afficher_erreur_inattendue, traiter_erreur_sqlite
from ui.repetition.constants import CM_VERS_M
from utils.logging_config import obtenir_logger


logger = obtenir_logger("ui.repetition_dialog")


class RepetitionActionsMixin:

    def _on_outil_change(self, event=None):
        cle = self.outil_var.get()
        outil = self.outil_map.get(cle) if cle else None
        self._mettre_a_jour_champs(outil)
        self._dessiner_schema(outil)

    def _mettre_a_jour_champs(self, outil):
        """Active les mesures utiles pour l'outil sélectionné."""
        for entry in self.entries.values():
            entry.configure(state="normal")

        if outil is None:
            champs_desactives = ("volume_eau", "h_debut", "h_fin")
        elif outil.type_outil == "entonnoir":
            champs_desactives = ("h_debut", "h_fin")
        else:
            champs_desactives = ("volume_eau",)

        for cle in champs_desactives:
            self.entries[cle].configure(state="disabled")

    def lire_float_cm(self, cle):
        """Lit un champ saisi en cm et le retourne converti en mètres."""
        val = self.entries[cle].get().strip()
        if not val:
            return None
        return float(val) * CM_VERS_M

    def lire_float_brut(self, cle):
        """Lit un champ sans conversion d'unité (ex. temps, volume)."""
        val = self.entries[cle].get().strip()
        return float(val) if val else None

    def _materiel_selectionne(self):
        outil_cle = self.outil_var.get()
        sonde_cle = self.sonde_var.get()
        if not outil_cle:
            messagebox.showerror("Champ requis", "Veuillez choisir un outil.",
                                 parent=self.window)
            return None
        if not sonde_cle:
            messagebox.showerror("Champ requis", "Veuillez choisir une sonde.",
                                 parent=self.window)
            return None
        return self.outil_map[outil_cle], self.sonde_map[sonde_cle]

    def _calculer_k(self):
        try:
            materiel = self._materiel_selectionne()
            if materiel is None:
                return
            outil, sonde = materiel

            ha = self.lire_float_cm("hauteur_air")
            temps = self.lire_float_brut("temps_infiltration")

            service = CalculService()

            if outil.type_outil == "tuyau":
                self.k_calcule = service.calculer_k_tuyau(
                    ha=ha, temps=temps,
                    diametre_tuyau=outil.diametre_interieur,
                    hauteur_tuyau=outil.hauteur_tuyau,
                    h_debut=self.lire_float_cm("h_debut"),
                    h_fin=self.lire_float_cm("h_fin"),
                    longueur_crepine=sonde.longueur_crepine,
                    diametre_sonde=sonde.diametre_interieur,
                )
            else:
                volume_l = self.lire_float_brut("volume_eau")

                self.k_calcule = service.calculer_k_entonnoir(
                    ha=ha, temps=temps,
                    L1=outil.L1, L2=outil.L2,
                    D1=outil.D1, D2=outil.D2, D3=outil.D3,
                    volume_eau=volume_l * 0.001 if volume_l is not None else None,
                    longueur_crepine=sonde.longueur_crepine,
                    diametre_sonde=sonde.diametre_interieur,
                )

            self.k_label.configure(text=theme.format_k(self.k_calcule))

        except ValueError as e:
            messagebox.showerror("Valeurs incohérentes", str(e), parent=self.window)
        except (ArithmeticError, TypeError):
            logger.exception("Erreur technique pendant le calcul de K")
            afficher_erreur_inattendue(self.window)

    def _enregistrer(self):
        if self._enregistrement_en_cours:
            return

        self._enregistrement_en_cours = True
        self.bouton_enregistrer.configure(state="disabled")
        if self._confirmation_after_id is not None:
            self.window.after_cancel(self._confirmation_after_id)
            self._confirmation_after_id = None
        self.confirmation_label.configure(text="")
        try:
            materiel = self._materiel_selectionne()
            if materiel is None:
                return
            outil, sonde = materiel

            rep = Repetition(
                point_id=int(self.point_id),
                sonde_id=sonde.id,
                outil_id=outil.id,
                methode=outil.type_outil,
                profondeur_enfoncement=self.lire_float_cm("profondeur_enfoncement"),
                hauteur_eau=self.lire_float_cm("hauteur_eau"),
                hauteur_air=self.lire_float_cm("hauteur_air"),
                temps_infiltration=self.lire_float_brut("temps_infiltration"),
                volume_eau=(self.lire_float_brut("volume_eau")
                            if outil.type_outil == "entonnoir" else None),
                h_debut=(self.lire_float_cm("h_debut")
                         if outil.type_outil == "tuyau" else None),
                h_fin=(self.lire_float_cm("h_fin")
                       if outil.type_outil == "tuyau" else None),
                k_calcule=self.k_calcule,
                commentaire=self.commentaire_text.get("1.0", tk.END).strip(),
            )

            if self.repetition:
                rep.id = self.repetition.id
                self.repo.modifier(rep)
            else:
                self.repo.ajouter(rep)

            if self.refresh_callback:
                self.refresh_callback()

            if self.repetition:
                self.window.destroy()
            else:
                self._preparer_repetition_suivante()

        except ValueError as e:
            messagebox.showerror("Valeurs incohérentes", str(e), parent=self.window)
        except (sqlite3.IntegrityError, sqlite3.OperationalError,
                sqlite3.DatabaseError) as erreur:
            traiter_erreur_sqlite(
                erreur, self.window, "l'enregistrement de la répétition"
            )
        finally:
            if self.window.winfo_exists():
                self.window.after(300, self._reactiver_enregistrement)

    def _reactiver_enregistrement(self):
        """Réactive l'enregistrement une fois le double-clic écarté."""
        self._enregistrement_en_cours = False
        if self.window.winfo_exists():
            self.bouton_enregistrer.configure(state="normal")

    def _preparer_repetition_suivante(self):
        """Conserve les valeurs utiles et attend une nouvelle mesure."""
        self.entries["temps_infiltration"].delete(0, tk.END)
        self.k_calcule = None
        self.k_label.configure(text="—")
        self.confirmation_label.configure(
            text="Répétition enregistrée. Vous pouvez saisir la suivante."
        )
        self._confirmation_after_id = self.window.after(
            2000, self._effacer_confirmation
        )
        self.entries["temps_infiltration"].focus_set()

    def _effacer_confirmation(self):
        """Efface le message de confirmation après son affichage."""
        self._confirmation_after_id = None
        if self.window.winfo_exists():
            self.confirmation_label.configure(text="")
