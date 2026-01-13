import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import base64, io, numpy

from mpl_toolkits.axes_grid1 import make_axes_locatable


class Histogram:
    """
    A 2DHistogram Class to handle all the plotting logic for the RAYX Web App.
    """

    def __init__(self, dataX, dataY, xLabel="No label", yLabel="No label"):
        self.dataX = list(dataX)
        self.dataY = list(dataY)

        self.xlabel = xLabel
        self.ylabel = yLabel

        self.ONE_D_HIST_SIZE = "15"

        if len(self.dataX) != len(self.dataY):
            raise ValueError(
                f"x and y must have same length, got {len(self.dataX)} and {len(self.dataY)}"
            )

    def GetPlotDataBase64(self) -> str:
        
        # "FD" calculation TODO: Search for something that fits better in a 2D histogram
        x = numpy.array(self.dataX)
        y = numpy.array(self.dataY)

        x_edges = numpy.histogram_bin_edges(x, bins='fd')
        y_edges = numpy.histogram_bin_edges(y, bins='fd')
        
        fig, ax = plt.subplots()
        h = ax.hist2d(self.dataX, self.dataY, bins=[x_edges, y_edges])
        fig.colorbar(h[3], ax=ax)

        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)

        # Construct 1D histograms
        divider = make_axes_locatable(ax)
        ax_hist_x = divider.append_axes("bottom", pad=0.3, size="15%", sharex=ax)
        ax_hist_y = divider.append_axes("left", pad=0.3, size="15%", sharey=ax)

        ax_hist_x.hist(self.dataX, bins="fd", histtype="step")
        ax_hist_y.hist(self.dataY, bins="fd", histtype="step", orientation="horizontal")

        # Save figure to buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)

        plt.close(fig)

        return base64.b64encode(buf.getvalue()).decode("ascii")
