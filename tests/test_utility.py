#!/usr/bin/env python3

import pytest

import numpy as np
import math

import matplotlib
matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from labelmaker.utility import within_tolerance, axis_lengths, closest

def create_test_plot():
    fig, ax = plt.subplots()

    x = np.arange(0, 20, 1)
    y = np.arange(-50, 50, 5)
    newline = Line2D(x, y, marker='o', linestyle='--', color='b', ms=5, mec='black',
                                mew=2,
                                markerfacecolor='black', fillstyle='full', picker=5)
    ax.add_line(newline)
    return fig, ax

def test_within_tolerance():
    _, ax = create_test_plot()
    dx, dy = axis_lengths(ax)

    # The threshold of 0.01 gives a threshold distance of 0.0141421
    assert within_tolerance(0.005, dx, dy, 0.01)
    # The threshold of 0.05 gives a threshold distance of 0.0707106
    assert within_tolerance(0.05, dx, dy, 0.05)

def test_outside_tolerance():
    _, ax = create_test_plot()
    dx, dy = axis_lengths(ax)
    # The threshold of 0.01 gives a threshold distance of 0.0141421
    assert not within_tolerance(0.02, dx, dy, 0.01)
    # The threshold of 0.05 gives a threshold distance of 0.0707106
    assert not within_tolerance(0.08, dx, dy, 0.05)

def test_closest_value():
    xdata = np.arange(-10, 10, 1)
    ydata = [math.sin(x) for x in xdata]
    dx = abs(max(xdata) - min(xdata))
    dy = abs(max(ydata) - min(ydata))

    assert 10 == closest(0, 0, xdata, ydata, dx, dy)[0]
    assert 13 == closest(4, 0.14, xdata, ydata, dx, dy)[0]
    assert 13 == closest(3, 0, xdata, ydata, dx, dy)[0]
