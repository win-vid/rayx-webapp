import matplotlib.pyplot as plt
import base64, io


class Plot:
    """
    A Plot Class to handle all the plotting logic for the RAYX Web App.
    If no title, x-label or y-label is given, they will be set to "No title", "No label", "No label"
    """

    def __init__(self, dataX, dataY, title="No title", xLabel="No label", yLabel="No label"):
        
        # Data
        self.dataX = list(dataX)
        self.dataY = list(dataY)
        
        # Interface
        self.title = title
        self.xlabel = xLabel
        self.ylabel = yLabel

        if len(self.dataX) != len(self.dataY):
            raise ValueError(
                f"x and y must have same length, got {len(self.dataX)} and {len(self.dataY)}"
            )

    def SetTitle(self, title):
        self.title = title

    def GetPlotDataBase64(self) -> str:
        """
        Returns the plot as a base64 string. Ideal for the Web App.
        """

        fig = plt.figure()
        plt.plot(self.dataX, self.dataY)
        plt.title(self.title)
        plt.xlabel("Ray index")
        plt.ylabel("Position X")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return base64.b64encode(buf.getvalue()).decode("ascii")
