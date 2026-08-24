"""API publique compatible des graphiques HydroK."""

from ui.charts.bar_charts import (
    graphique_barres_k_par_point,
    graphique_repartition_methodes,
    graphique_repartition_profondeurs,
    graphique_repetitions_par_profondeur,
    graphique_repetitions_point,
)
from ui.charts.boxplots import graphique_boxplot_k_par_point
from ui.charts.core import nouvelle_figure
from ui.charts.histograms import graphique_histogramme
from ui.charts.maps import graphique_carte_points
from ui.charts.pie_charts import graphique_repartition_facies
from ui.charts.rendering import (
    inserer_figure,
    rendre_figure_png,
    soumettre_rendu_figure_png,
)


__all__ = (
    "graphique_barres_k_par_point",
    "graphique_boxplot_k_par_point",
    "graphique_carte_points",
    "graphique_histogramme",
    "graphique_repartition_facies",
    "graphique_repartition_methodes",
    "graphique_repartition_profondeurs",
    "graphique_repetitions_par_profondeur",
    "graphique_repetitions_point",
    "inserer_figure",
    "nouvelle_figure",
    "rendre_figure_png",
    "soumettre_rendu_figure_png",
)
