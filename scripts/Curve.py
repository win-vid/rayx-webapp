#region Imports
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scripts.HistogramData import HistogramData
# endregion


class Curve:
    """
    A curve plot (e.g. reflectivity vs photon energy).
    Uses Plotly for interactive visualization.
    """

    def __init__(self, dataX, dataY, xLabel="No label", yLabel="No label", title="No title", incoming=[], outgoing=[], incoming_efields=[], outgoing_efields=[]):

        self.curveDataX = np.array(dataX)
        self.curveDataY = np.array(dataY)

        self.incoming = np.array(incoming)
        self.outgoing = np.array(outgoing)

        self.incoming_efields = incoming_efields
        self.outgoing_efields = outgoing_efields

        self.xlabel = xLabel
        self.ylabel = yLabel
        self.title = title

        self.plot_html = self.GetPlotHTML()

    def GetPlotHTML(self) -> str:
        """
        Returns interactive Plotly HTML for a curve plot. For better debugging this class also plots a table of the data points.
        """

        # Create figure
        fig = make_subplots(
            rows=3, cols=1,
            row_heights=[0.5, 0.25, 0.25],  # main vs table
            vertical_spacing=0.1,
            specs=[
                [{"type": "xy"}],      # row 1: the curve
                [{"type": "domain"}],   # row 2: the table
                [{"type": "domain"}]   # row 3: the table
            ]
        )

        # Add reflectivity curve
        fig.add_trace(
            go.Scatter(
                x=self.curveDataX,
                y=self.curveDataY,
                mode="lines",
                name="Reflectivity"
            ), row=1, col=1
        )

        # Add data table
        fig.add_trace(
            go.Table(
                header=dict(values=["Photon Energy (eV)", "Reflectivity"]),
                cells=dict(values=[self.curveDataX, self.curveDataY])
            ), row=2, col=1
        )

        # E-field table
        fig.add_trace(
            go.Table(
                header=dict(values=["eV", "In Ex", "In Ey", "In Ez", "Out Ex", "Out Ey", "Out Ez"]),
                cells=dict(values=[
                    self.curveDataX,
                    [e.get("ex", float("nan")) for e in self.incoming_efields],
                    [e.get("ey", float("nan")) for e in self.incoming_efields],
                    [e.get("ez", float("nan")) for e in self.incoming_efields],
                    [e.get("ex", float("nan")) for e in self.outgoing_efields],
                    [e.get("ey", float("nan")) for e in self.outgoing_efields],
                    [e.get("ez", float("nan")) for e in self.outgoing_efields],
                ])
            ), row=3, col=1
        )

        # Layout
        fig.update_layout(
            height=1000,
            width=1000,
            title=self.title,
            xaxis_title=self.xlabel,
            yaxis_title=self.ylabel,
            showlegend=False,
            dragmode="pan",
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