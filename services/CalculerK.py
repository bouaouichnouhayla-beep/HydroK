import numpy as np
import sympy as sy

# Calcul selon Datry (2015) avec trois compartiments d'entonnoir.

def Datry(ha, ta, L1, L2, D1, D2, D3, V_verse, longueur_crepine=0.18, diametre_sonde=0.02):
    # Valeurs historiques de la sonde Tube HC18, utilisées comme repli.

    global K, h0

    if ta is None or ta <= 0:
        raise ValueError("Le temps d'infiltration (ta) doit être strictement positif.")
    if ha is None or ha < 0:
        raise ValueError("La hauteur d'air (ha) ne peut pas être négative.")
    if V_verse is None or V_verse <= 0:
        raise ValueError("Le volume d'eau versé doit être strictement positif.")

    L = longueur_crepine if longueur_crepine else 0.18   # m
    D = diametre_sonde if diametre_sonde else 0.02       # m

    if L <= 0 or D <= 0:
        raise ValueError("La longueur de crépine et le diamètre de la sonde doivent être positifs.")

    C = 2 * np.pi * L / (np.log(L / D + (1 + (L / D) ** 2) ** 0.5)) - 2.75 * D
    D_t = D

    V0 = V_verse  # m³
    Ta = ta  # s
    h_ini = 0.5  # m
    H = 1.2  # m

    Ha = ha  # m

    Li = np.array([L1, L2, 0])
    Di = np.array([D1, D2, D3])

    ai = np.zeros(len(Di))
    ai[0] = (Di[1] - Di[0]) / Li[0]
    ai[1] = (Di[2] - Di[1]) / Li[1]
    ai[2] = 0

    Vi = np.zeros(len(Di))
    Vi[0] = np.pi * Li[0] / (12 * (Di[1] - Di[0])) * (Di[1] ** 3 - Di[0] ** 3)
    Vi[1] = np.pi * Li[1] / (12 * (Di[2] - Di[1])) * (Di[2] ** 3 - Di[1] ** 3)
    Vi[2] = 0

    Vt = np.pi * D_t ** 2 / 4 * Ha

    if V_verse > Vi[0] + Vi[1]:
        h0 = 4 * (V0 - Vt - Vi[0] - Vi[1]) / (np.pi * Di[2]**2) + Ha + Li[0] + Li[1]

        b1 = Di[0] - (Di[1] - Di[0]) / Li[0] * Ha
        b2 = Di[1] - (Di[2] - Di[1]) / Li[1] * Ha - (Di[2] - Di[1]) / Li[1] * Li[0]
        b3 = Di[2]

        h11 = Ha + Li[0]
        h12 = Ha
        h21 = Ha + Li[0] + Li[1]
        h22 = Ha + Li[0]
        h31 = h0
        h32 = Ha + Li[0] + Li[1]

        S11 = (ai[0]**2 * h11**2) / 2 + 2 * ai[0] * b1 * h11 + b1**2 * np.log(h11)
        S12 = (ai[0]**2 * h12**2) / 2 + 2 * ai[0] * b1 * h12 + b1**2 * np.log(h12)
        S21 = (ai[1]**2 * h21**2) / 2 + 2 * ai[1] * b2 * h21 + b2**2 * np.log(h21)
        S22 = (ai[1]**2 * h22**2) / 2 + 2 * ai[1] * b2 * h22 + b2**2 * np.log(h22)
        S31 = (ai[2]**2 * h31**2) / 2 + 2 * ai[2] * b3 * h31 + b3**2 * np.log(h31)
        S32 = (ai[2]**2 * h32**2) / 2 + 2 * ai[2] * b3 * h32 + b3**2 * np.log(h32)

        Stot = S11 - S12 + S21 - S22 + S31 - S32

        K = np.pi / (4 * C * Ta) * Stot

    elif V_verse <= Vi[0] + Vi[1]:
        # Résolution cubique lorsque le troisième compartiment n'est pas atteint.

        x = sy.Symbol('x')

        eq = sy.Eq(np.pi/12*(((Di[2]-Di[1])/Li[1]*(x-Ha-Li[0])+Di[1])**3-Di[1]**3) - (V0-Vt-Vi[0])*((Di[2]-Di[1])/Li[1]), 0)

        solution = sy.solve( eq )
        h0 = solution[0]

        b1 = Di[0] - (Di[1] - Di[0]) / Li[0] * Ha
        b2 = Di[1] - (Di[2] - Di[1]) / Li[1] * Ha - (Di[2] - Di[1]) / Li[1] * Li[0]
        b3 = Di[2]

        h11 = Ha + Li[0]
        h12 = Ha

        h21 = float(h0)

        h22 = Ha + Li[0]

        S11 = (ai[0]**2 * h11**2) / 2 + 2 * ai[0] * b1 * h11 + b1**2 * np.log(h11)
        S12 = (ai[0]**2 * h12**2) / 2 + 2 * ai[0] * b1 * h12 + b1**2 * np.log(h12)
        S21 = (ai[1]**2 * h21**2) / 2 + 2 * ai[1] * b2 * h21 + b2**2 * np.log(h21)
        S22 = (ai[1]**2 * h22**2) / 2 + 2 * ai[1] * b2 * h22 + b2**2 * np.log(h22)

        Stot = S11 - S12 + S21 - S22

        K = np.pi / (4 * C * Ta) * Stot

    return K, h0

# Variante utilisant un tuyau.
def InfiltrationTuyau(ha, ta, D_tuyau, H_tuyau, H_debut, H_fin, longueur_crepine,
diametre_sonde):
    # Post-traitement selon Datry et al. (2014).
    L = longueur_crepine
    D = diametre_sonde

    if ta is None or ta <= 0:
        raise ValueError("Le temps d'infiltration (ta) doit être strictement positif.")
    if L is None or L <= 0:
        raise ValueError("La longueur de crépine de la sonde doit être strictement positive.")
    if D is None or D <= 0:
        raise ValueError("Le diamètre intérieur de la sonde doit être strictement positif.")
    if D_tuyau is None or D_tuyau <= 0:
        raise ValueError("Le diamètre du tuyau doit être strictement positif.")
    if H_debut is None or H_fin is None:
        raise ValueError("Les hauteurs de début et de fin (h_début, h_fin) sont obligatoires.")

    C = 2 * np.pi * L / (np.log(L / D + (1 + (L / D)**2)**0.5)) - 2.75 * D
    D_t = D

    h_tuyau = H_tuyau  # m
    d_tuyau = D_tuyau  # m

    Ta = ta  # s
    Ha = ha  # m
    h_debut = H_debut
    h_fin = H_fin

    h1 = Ha + h_tuyau - (h_tuyau - h_debut)
    h2 = Ha + h_fin

    if h1 <= 0 or h2 <= 0:
        raise ValueError(
            "Les hauteurs calculées (h1, h2) doivent être strictement positives. "
            "Vérifiez les valeurs de h_début, h_fin et hauteur d'air saisies."
        )

    K = np.pi * d_tuyau**2 / (4 * C * Ta) * (np.log(h1) - np.log(h2))

    if K < 0:
        raise ValueError(
            "Le calcul donne une conductivité K négative : vérifiez que h_début "
            "est bien supérieur à h_fin (la hauteur d'eau doit diminuer dans le temps)."
        )

    return K


def calculer_k_repetition(repetition, outil, sonde):
    """Calcule K selon l'outil et la sonde de la répétition."""

    if sonde is None:
        raise ValueError("Une sonde doit être fournie pour calculer K.")

    if repetition.methode == "entonnoir":

        k, h0 = Datry(
            ha=repetition.hauteur_air,
            ta=repetition.temps_infiltration,
            L1=outil.L1,
            L2=outil.L2,
            D1=outil.D1,
            D2=outil.D2,
            D3=outil.D3,
            V_verse=repetition.volume_eau,
            longueur_crepine=sonde.longueur_crepine,
            diametre_sonde=sonde.diametre_interieur,
        )

        return k

    elif repetition.methode == "tuyau":

        k = InfiltrationTuyau(
            ha=repetition.hauteur_air,
            ta=repetition.temps_infiltration,
            D_tuyau=outil.diametre_interieur,
            H_tuyau=outil.hauteur_tuyau,
            H_debut=repetition.h_debut,
            H_fin=repetition.h_fin,
            longueur_crepine=sonde.longueur_crepine,
            diametre_sonde=sonde.diametre_interieur,
        )

        return k

    else:
        raise ValueError("Méthode inconnue")
