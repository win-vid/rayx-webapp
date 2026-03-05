#region Imports
import numpy as np
import plotly.graph_objects as go
from HistogramData import HistogramData
# endregion


class Curve:
    """
    A curve plot (e.g. reflectivity vs photon energy).
    Uses Plotly for interactive visualization.
    """

    def __init__(self, dataX, dataY, xLabel="No label", yLabel="No label", title="No title"):

        self.curveDataX = np.array(dataX)
        self.curveDataY = np.array(dataY)

        self.xlabel = xLabel
        self.ylabel = yLabel
        self.title = title

        self.plot_html = self.GetPlotHTML()

    def GetPlotHTML(self) -> str:
        """
        Returns interactive Plotly HTML for a curve plot.
        """

        # Create figure
        fig = go.Figure()

        # Add reflectivity curve
        fig.add_trace(
            go.Scatter(
                x=self.curveDataX,
                y=self.curveDataY,
                mode="lines+markers",
                name="Reflectivity"
            )
        )

        # Layout
        fig.update_layout(
            height=800,
            width=800,
            title=self.title,
            xaxis_title=self.xlabel,
            yaxis_title=self.ylabel,
            showlegend=False
        )

        # Controls
        fig.update_layout(
            dragmode="pan"
        )

        # Return HTML
        return fig.to_html(
            full_html=False,
            include_plotlyjs="cdn",
            config={
                "scrollZoom": True,
                "doubleClick": "reset",
                "displaylogo": False
            }
        )