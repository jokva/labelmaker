import math

def within_tolerance(distance, dx, dy, threshold):
    """
    Verify if the distance is within the threshold given dx,dy
    :param distance: float
    :param dx: float
    :param dy: float
    :param threshold: float
    :return: boolean
    """
    maxdx = math.pow((dx * threshold), 2)
    maxdy = math.pow((dy * threshold), 2)

    return distance < math.sqrt(maxdx + maxdy)

def axis_lengths(ax):
    """
    Takes a matplotlib axis and returns the length of the axes
    :param ax: The Axes instance to find the lengths of
    :return: length of x and y axis
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    dx = abs(xlim[1] - xlim[0])
    dy = abs(ylim[1] - ylim[0])
    return dx, dy

def abslist(value, valuerange):
    """
    Takes a value and a list and returns a list of absolute differences for each element
    :param value: float
    :param valuerange: list of floats
    :return: list of floats
    """
    return [abs(x - value) for x in valuerange]

def closest(x, y, xdata, ydata, dx, dy):
    """
    Returns the index of the sample that from xdata and ydata
    that is closest to input x and y
    :param x: double x-point
    :param y: double y-point
    :param xdata: [list] range of x-points
    :param ydata: [list] range of y-points
    :param dx: x-axis length
    :param dy: y-axis length
    :return: (index, distance)
    """
    diff_xdata = [x/dx for x in abslist(x, xdata)]
    diff_ydata = [y/dy for y in abslist(y, ydata)]
    squared = [math.sqrt(pow(a, 2) + pow(b, 2)) for a, b in zip(diff_xdata, diff_ydata)]

    min_distance = min(squared)
    return squared.index(min_distance), min_distance


