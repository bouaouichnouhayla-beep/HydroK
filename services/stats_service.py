import statistics


def calculer_moyenne_k(repetitions):
    valeurs_k = [
        r.k_calcule for r in repetitions
        if r.k_calcule is not None
    ]

    if len(valeurs_k) == 0:
        return None

    return statistics.mean(valeurs_k)


def calculer_ecart_type_k(repetitions):
    valeurs_k = [
        r.k_calcule for r in repetitions
        if r.k_calcule is not None
    ]

    if len(valeurs_k) < 2:
        return 0

    return statistics.stdev(valeurs_k)


def calculer_coefficient_variation(repetitions):
    moyenne = calculer_moyenne_k(repetitions)
    ecart_type = calculer_ecart_type_k(repetitions)

    if moyenne is None or moyenne == 0:
        return None

    return (ecart_type / moyenne) * 100


def detecter_valeurs_aberrantes(repetitions, seuil_sigma=2):
    moyenne = calculer_moyenne_k(repetitions)
    ecart_type = calculer_ecart_type_k(repetitions)

    if moyenne is None or ecart_type == 0:
        return repetitions

    for repetition in repetitions:
        if repetition.k_calcule is not None:
            distance = abs(repetition.k_calcule - moyenne)

            if distance > seuil_sigma * ecart_type:
                repetition.est_aberrante = True
            else:
                repetition.est_aberrante = False

    return repetitions