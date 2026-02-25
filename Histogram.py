#region Imports
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from HistogramData import HistogramData
# endregion

class Histogram:
    """
    A 2DHistogram Class to handle all the plotting logic
    for a single element for the RAYX Web App. Plots are plotted
    using Plotly.
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

        countsX, edgesX = np.histogram(dataX, bins="fd")
        countsY, edgesY = np.histogram(dataY, bins="fd")

        # region Plot
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.15, 0.85],  # main vs side
            row_heights=[0.85, 0.15],    # main vs bottom
            specs=[
                [{"type": "histogram"}, {"type": "histogram2d"}],  # side + main 2d histogram
                [None, {"type": "histogram"}]                      # bottom histogram
            ],
            horizontal_spacing=0.02,
            vertical_spacing=0.02
        )
        # Link x of bottom histogram to main histogram
        fig.update_xaxes(
            matches='x2', 
            row=2, col=2, 
            title_text=self.xlabel)

        # Link y of side histogram to main histogram
        fig.update_yaxes(
            matches='y2',
            row=1, col=1, 
            title_text=self.ylabel
        )

        # Remove numbers on main histogram
        fig.update_xaxes(showticklabels=False, ticks="outside", ticklen=6, row=1, col=2)
        fig.update_yaxes(showticklabels=False, ticks="outside", ticklen=6, row=1, col=2)

        # Main 2D histogram
        fig.add_trace(go.Histogram2d(x=dataX, y=dataY, nbinsx=bins[0], nbinsy=bins[1],
                                    colorscale="Viridis"), row=1, col=2)

        # Side histogram (Y marginal)
        fig.add_trace(go.Histogram(
            y=dataY, 
            ybins=dict(
                start=edgesY[0],
                end=edgesY[-1],
                size=edgesY[1] - edgesY[0]
            ),
            marker_color="cornflowerblue"), 
            row=1, col=1)

        # Bottom histogram (X marginal)
        fig.add_trace(go.Histogram(
            x=dataX, 
            xbins=dict(
                start=edgesX[0],
                end=edgesX[-1],
                size=edgesX[1] - edgesX[0]
            ),
            marker_color="cornflowerblue"), row=2, col=2)

        
        # Center of Mass line Side histogram
        fig.add_shape(
            type="line",
            x0=0,
            y0=self.histogramDataY.info["centerOfMass"],
            x1=self.histogramDataY.info["y"],
            y1=self.histogramDataY.info["centerOfMass"],
            line=dict(color="green", width=2),
            xref="x1",
            yref="y1"
        )

        # Center of Mass line Bottom histogram
        fig.add_shape(
            type="line",
            x0=self.histogramDataX.info["centerOfMass"],
            y0=0,
            x1=self.histogramDataX.info["centerOfMass"],
            y1=self.histogramDataX.info["y"],
            line=dict(color="green", width=2),
            xref="x3",
            yref="y3"
        )

        # FWHM lines side histogram
        fig.add_shape(
            type="line",
            x0=self.histogramDataY.info["y"],
            y0=self.histogramDataY.info["x1"],
            x1=self.histogramDataY.info["y"],
            y1=self.histogramDataY.info["x2"],
            line=dict(color="orange", width=2),
            xref="x1",
            yref="y1"
        )

        fig.add_shape(
            type="line",
            x0=0,
            y0=self.histogramDataY.info["x1"],
            x1=self.histogramDataY.info["y"],
            y1=self.histogramDataY.info["x1"],
            line=dict(color="orange", width=2),
            xref="x1",
            yref="y1"
        )

        fig.add_shape(
            type="line",
            x0=0,
            y0=self.histogramDataY.info["x2"],
            x1=self.histogramDataY.info["y"],
            y1=self.histogramDataY.info["x2"],
            line=dict(color="orange", width=2),
            xref="x1",
            yref="y1"
        )

        

        # FWHM lines bottom histogram
        fig.add_shape(
            type="line",
            x0=self.histogramDataX.info["x1"],
            y0=self.histogramDataX.info["y"],
            x1=self.histogramDataX.info["x2"],
            y1=self.histogramDataX.info["y"],
            line=dict(color="orange", width=2),
            xref="x3",
            yref="y3"
        )

        fig.add_shape(
            type="line",
            x0=self.histogramDataX.info["x1"],
            y0=0,
            x1=self.histogramDataX.info["x1"],
            y1=self.histogramDataX.info["y"],
            line=dict(color="orange", width=2),
            xref="x3",
            yref="y3"
        )

        fig.add_shape(
            type="line",
            x0=self.histogramDataX.info["x2"],
            y0=0,
            x1=self.histogramDataX.info["x2"],
            y1=self.histogramDataX.info["y"],
            line=dict(color="orange", width=2),
            xref="x3",
            yref="y3"
        )        

        # Update layout
        fig.update_layout(
            height=800,
            width=800,
            title=self.title,
            showlegend=False,
            bargap=0.05
        )
        # endregion

        # region controls
        fig.update_layout(
            dragmode="pan"
        )
        # endregion

        # Return embeddable HTML
        return fig.to_html(
            full_html=False, 
            include_plotlyjs="cdn",
            config={
                "scrollZoom": True,      # wheel zoom
                "doubleClick": "reset",  # double-click resets
                "displaylogo": False     # remove Plotly logo
            }
        )