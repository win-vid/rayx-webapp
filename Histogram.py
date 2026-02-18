import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from HistogramData import HistogramData


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

        self.plot_html = self.GetPlotHTML()

    def GetPlotHTML(self) -> str:
        """
        Returns interactive Plotly HTML.
        It assumes that this plot is a 2D histogram and constructs a 2D histogram.
        """

        dataX = np.asarray(self.histogramDataX.data)
        dataY = np.asarray(self.histogramDataY.data)

        # "FD" calculation TODO: Search for something that fits better in a 2D histogram
        bins = [min(200, len(dataX)//20), min(200, len(dataY)//20)] # bins[0] = x, bins[1] = y

        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.85, 0.15],  # main vs side
            row_heights=[0.85, 0.15],    # main vs bottom
            specs=[
                [{"type": "histogram2d"}, {"type": "histogram"}],  # main 2D + side
                [{"type": "histogram"}, None]                       # bottom histogram
            ],
            horizontal_spacing=0.02,
            vertical_spacing=0.02
        )
        # Link x of bottom histogram to main histogram
        fig.update_xaxes(matches='x1', row=2, col=1)

        # Link y of side histogram to main histogram
        fig.update_yaxes(matches='y1', row=1, col=2)

        # Explicitly set domains to prevent overlap
        fig.update_xaxes(domain=[0, 0.85], row=1, col=1)  # main 2D
        fig.update_yaxes(domain=[0, 0.85], row=1, col=1)

        fig.update_xaxes(domain=[0, 0.85], row=2, col=1)  # bottom histogram x domain
        fig.update_yaxes(domain=[0, 0.85], row=1, col=2)  # side histogram y domain


        # Main 2D histogram
        fig.add_trace(go.Histogram2d(x=dataX, y=dataY, nbinsx=bins[0], nbinsy=bins[1],
                                    colorscale="Viridis"), row=1, col=1)

        # Side histogram (Y marginal)
        fig.add_trace(go.Histogram(y=dataY, nbinsy=bins[1],
                                marker_color="cornflowerblue"), row=1, col=2)

        # Bottom histogram (X marginal)
        fig.add_trace(go.Histogram(x=dataX, nbinsx=bins[0],
                                marker_color="cornflowerblue"), row=2, col=1)





        fig.update_layout(
            height=800,
            width=800,
            title=self.title,
            showlegend=False,
            bargap=0.05
        )

        # Return embeddable HTML
        return fig.to_html(full_html=False, include_plotlyjs="cdn")