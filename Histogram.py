import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import base64, io, numpy

from mpl_toolkits.axes_grid1 import make_axes_locatable
from HistogramData import HistogramData

# TODO: Currently the histogram can't decide which axis to correctly use

class Histogram:
    """
    A 2DHistogram Class to handle all the plotting logic
    for a single element for the RAYX Web App.
    """

    def __init__(self, dataX, dataY, xLabel="No label", yLabel="No label", title="No title"):

        # Construct HistogramData for x and y
        self.histogramDataX = HistogramData(dataX)
        self.histogramDataY = HistogramData(dataY)

        # Full width half maximum x and y
        self.fwhmX = self.histogramDataX.info["fwhm"]
        self.fwhmY = self.histogramDataY.info["fwhm"]

        # Histogram customization
        self.xlabel = xLabel
        self.ylabel = yLabel
        self.title = title

        self.line_color = "orange"

        if len(self.histogramDataX.data) != len(self.histogramDataY.data):
            raise ValueError(
                f"x and y must have same length, got "
                f"{len(self.histogramDataX.data)} and {len(self.histogramDataY.data)}"
            )
        
        self.plot_image = self.GetPlotDataBase64()

    def GetPlotDataBase64(self) -> str:
        """
        Returns a base64 encoded string of the plot. This is used to send the plot to the client.
        It assumes that this plot is a 2D histogram and constructs a 2D histogram.
        """

        dataX = self.histogramDataX.data
        dataY = self.histogramDataY.data

        # "FD" calculation TODO: Search for something that fits better in a 2D histogram
        x = numpy.asarray(dataX)
        y = numpy.asarray(dataY)

        # TODO: I dont know if this is correct
        bins = [min(200, len(dataX)//20), min(200, len(dataY)//20)]

        # Construct 2D-Histogram
        hist, xedges, yedges = numpy.histogram2d(
            x, y,
            bins=bins,       # TODO: Implement fd calculation
            density=True
        )

        extent = [
            xedges[0], xedges[-1],
            yedges[0], yedges[-1]
        ]

        fig, ax = plt.subplots()

        h = ax.imshow(
            hist.T,
            extent=extent,
            origin="lower",
            aspect="auto",
            cmap="viridis",
            interpolation="nearest"
        )

        # Add colorbar
        fig.colorbar(
            h, 
            ax=ax, 
            location="left",
            pad=.15
        )

        # Set Labels & Title
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        ax.set_title(self.title)

        # Construct 1D-histograms for x- and y-axis
        divider = make_axes_locatable(ax)

        ax_hist_x = divider.append_axes(
            "bottom",
            pad=0.3,
            size="15%",
            sharex=ax
        )
        ax_hist_x.set_xlabel(self.xlabel)

        ax_hist_y = divider.append_axes(
            "right",
            pad=0.3,
            size="15%",
            sharey=ax
        )
        #ax_hist_y.set_ylabel(self.ylabel)

        ax_hist_y.invert_xaxis() 
        ax_hist_y.yaxis.set_ticks_position("right")
        ax_hist_y.yaxis.set_label_position("right")

        ax_hist_x.hist(dataX, bins="fd", histtype="step")
        ax_hist_y.hist(dataY, bins="fd", histtype="step", orientation="horizontal")

        # Draw FWHM-lines for Histogram X
        ax_hist_x.plot(
            [self.histogramDataX.info["x1"], self.histogramDataX.info["x2"]],
            [self.histogramDataX.info["y"], self.histogramDataX.info["y"]],
            '--', lw=1, color='red'
        )
        ax_hist_x.plot(
            [self.histogramDataX.info["x1"], self.histogramDataX.info["x1"]],
            [0, self.histogramDataX.info["y"]],
            '--', lw=1, color=self.line_color
        )
        ax_hist_x.plot(
            [self.histogramDataX.info["x2"], self.histogramDataX.info["x2"]],
            [0, self.histogramDataX.info["y"]],
            '--', lw=1, color=self.line_color
        )

        # Draw FWHM-lines for Histogram Y
        ax_hist_y.plot(
            [self.histogramDataY.info["y"], self.histogramDataY.info["y"]],
            [self.histogramDataY.info["x1"], self.histogramDataY.info["x2"]],
            '--', lw=1, color='red'
        )

        ax_hist_y.hlines(
            [self.histogramDataY.info["x1"], self.histogramDataY.info["x2"]],
            xmin=0,
            xmax=self.histogramDataY.info["y"],
            colors=self.line_color,
            linestyles='--',
            linewidth=1
        )

        # Draw centerOfMass point axes for Histogram X & Y
        ax_hist_x.axvline(
            self.histogramDataX.info["centerOfMass"],
            color="green",
            linewidth=1
        )

        ax_hist_y.axhline(
            self.histogramDataY.info["centerOfMass"],
            color="green",
            linewidth=1
        )

        # Save figure to buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)

        plt.close(fig)

        return base64.b64encode(buf.getvalue()).decode("ascii")