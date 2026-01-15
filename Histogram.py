import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import base64, io, numpy

from mpl_toolkits.axes_grid1 import make_axes_locatable
from HistogramData import HistogramData


class Histogram:
    """
    A 2DHistogram Class to handle all the plotting logic for the RAYX Web App.
    """

    def __init__(self, dataX, dataY, xLabel="No label", yLabel="No label", title="No title"):

        self.histogramDataX = HistogramData(dataX)
        self.histogramDataY = HistogramData(dataY)

        self.fwhmX = self.histogramDataX.fwhm
        self.fwhmY = self.histogramDataY.fwhm

        self.xlabel = xLabel
        self.ylabel = yLabel
        self.title = title

        self.line_color = "orange"

        if len(self.histogramDataX.data) != len(self.histogramDataY.data):
            raise ValueError(
                f"x and y must have same length, got {len(self.histogramDataX)} and {len(self.histogramDataY)}"
            )

    def GetPlotDataBase64(self) -> str:
        
        dataX = self.histogramDataX.data
        dataY = self.histogramDataY.data

        # "FD" calculation TODO: Search for something that fits better in a 2D histogram

        # Construct 2D-Histogram
        x = numpy.array(dataX)
        y = numpy.array(dataY)

        x_edges = numpy.histogram_bin_edges(x, bins='fd')
        y_edges = numpy.histogram_bin_edges(y, bins='fd')
        
        fig, ax = plt.subplots()
        h = ax.hist2d(dataX, dataY, bins=[x_edges, y_edges])
        ax.axis("off")

        fig.colorbar(h[3], ax=ax)

        # Set Lalels & Title
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        ax.set_title(self.title)

        # Construct 1D-histograms for x- and y-axis
        divider = make_axes_locatable(ax)
        
        ax_hist_x = divider.append_axes(
            "bottom", pad=0.3, 
            size="15%", 
            sharex=ax
        )
        ax_hist_x.set_xlabel(self.xlabel)
        
        ax_hist_y = divider.append_axes(
            "left", 
            pad=0.3, 
            size="15%", 
            sharey=ax
        )
        ax_hist_y.set_ylabel(self.ylabel)

        ax_hist_x.hist(dataX, bins="fd", histtype="step")
        ax_hist_y.hist(dataY, bins="fd", histtype="step", orientation="horizontal")

        # Draw FWHM-lines for Histogram X
        ax_hist_x.plot([self.histogramDataX.x1, self.histogramDataX.x2], [self.histogramDataX.y, self.histogramDataX.y], '--', lw=1, color='red')
        ax_hist_x.plot([self.histogramDataX.x1, self.histogramDataX.x1], [0, self.histogramDataX.y], '--', lw=1, color=self.line_color)
        ax_hist_x.plot([self.histogramDataX.x2, self.histogramDataX.x2], [0, self.histogramDataX.y], '--', lw=1, color=self.line_color)
        
        # Draw FWHM-lines for Histogram Y
        # vertical FWHM line (correct)
        ax_hist_y.plot(
            [self.histogramDataY.y, self.histogramDataY.y],
            [self.histogramDataY.x1, self.histogramDataY.x2],
            '--', lw=1, color='red'
        )

        # horizontal markers at x1 and x2
        ax_hist_y.hlines(
            [self.histogramDataY.x1, self.histogramDataY.x2],
            xmin=0,
            xmax=self.histogramDataY.y,
            colors=self.line_color,
            linestyles='--',
            linewidth=1
        )

        # Save figure to buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)

        plt.close(fig)

        return base64.b64encode(buf.getvalue()).decode("ascii")