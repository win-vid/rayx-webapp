import numpy as np


class HistogramData:
    """
    Stores data from a histogram, including the FWHM and the position of the FWHM.
    """

    # linear interpolation for precise position
    @staticmethod
    def interp_x(y1, y2, x1, x2, y_target):
        return x1 + (y_target - y1) * (x2 - x1) / (y2 - y1)

    # Get Full Width at Half Maximum of peak
    def GetFWHM(self, data) -> float:
        counts, bin_edges = np.histogram(data, bins="fd")

        # Get Maximum and half of maximum
        max_count = np.max(counts)
        half_max = max_count / 2
        self.y = half_max

        # middle of the bins
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # indices of bins with counts above half of maximum
        indices_above_half = np.where(counts >= half_max)[0]

        # safety check
        if len(indices_above_half) < 2:
            raise ValueError("Not enough data above half maximum to compute FWHM in HistogramData.py")

        left_index = indices_above_half[0]
        right_index = indices_above_half[-1]

        # left interpolation (guard against index underflow)
        if left_index == 0:
            self.x1 = bin_centers[0]
        else:
            self.x1 = self.interp_x(
                counts[left_index - 1],
                counts[left_index],
                bin_centers[left_index - 1],
                bin_centers[left_index],
                half_max
            )

        # right interpolation (guard against index overflow)
        if right_index == len(counts) - 1:
            self.x2 = bin_centers[-1]
        else:
            self.x2 = self.interp_x(
                counts[right_index],
                counts[right_index + 1],
                bin_centers[right_index],
                bin_centers[right_index + 1],
                half_max
            )

        return self.x2 - self.x1

    def GetFocus(self, data) -> float:
        """
        Returns the focus of the data. Data needs to be a histogram.
        """
        counts, bin_edges = np.histogram(data, bins="fd")

        # Area of histogram
        area = np.sum(counts)
        half_area = area / 2

        x_right = None
        x_left = None

        for i in range(len(bin_edges) - 1):
            if half_area < np.sum(counts[i:]):
                x_right = bin_edges[i]
                break

        for i in range(len(bin_edges) - 1, 0, -1):
            if half_area < np.sum(counts[:i]):
                x_left = bin_edges[i]
                break
        
        focus = (x_right + x_left) / 2
        
        # TODO: Refactor this
        self.focus_y = np.interp(focus, (bin_edges[:-1] + bin_edges[1:]) / 2, counts)

        return focus

    def __init__(self, data):
        self.data = list(data)
        self.x1 = None
        self.x2 = None
        self.y = None
        self.focus_y = None
        
        try:
            self.fwhm = self.GetFWHM(self.data)
            self.focus = self.GetFocus(self.data)
            print(self.focus)        
        except ValueError as e:
            print("Error calculating FWHM:", e)
            self.fwhm = 0.0
            self.focus = 0.0