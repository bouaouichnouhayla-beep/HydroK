"""Rendu Tkinter, PNG et asynchrone des figures Matplotlib."""

import io
from concurrent.futures import ThreadPoolExecutor

from ui import theme
from ui.charts.core import FigureCanvasAgg, FigureCanvasTkAgg, plt


_CHART_RENDER_EXECUTOR = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="hydrok-chart-render",
)


def inserer_figure(parent, fig, bg=None):
    """Intègre une figure Matplotlib dans un widget Tkinter."""
    if FigureCanvasTkAgg is None:
        raise RuntimeError(
            "matplotlib.backends.backend_tkagg indisponible : "
            "tkinter n'est pas installé dans cet environnement."
        )

    try:
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=bg or theme.SURFACE, highlightthickness=0, bd=0)
        widget._mpl_canvas = canvas  # garde une référence (évite le garbage collector)
        return widget
    finally:
        plt.close(fig)


def rendre_figure_png(figure_factory):
    """Construit une figure locale et la rend en PNG via Agg, sans objet Tk."""
    fig = None
    output = io.BytesIO()
    try:
        fig = figure_factory()
        canvas = FigureCanvasAgg(fig)
        canvas.print_png(output)
        return output.getvalue()
    finally:
        output.close()
        if fig is not None:
            fig.clear()


def soumettre_rendu_figure_png(figure_factory):
    """Soumet un rendu PNG au worker Matplotlib partagé de l'application."""
    return _CHART_RENDER_EXECUTOR.submit(rendre_figure_png, figure_factory)
