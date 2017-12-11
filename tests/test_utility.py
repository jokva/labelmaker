#!/usr/bin/env python3

import unittest

import numpy as np
import math

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from utility import within_tolerance, axis_lengths, closest

class TestUtility(unittest.TestCase):
    def create_test_plot(self):
        fig, ax = plt.subplots()

        x = np.arange(0, 20, 1)
        y = np.arange(-50, 50, 5)
        newline = Line2D(x, y, marker='o', linestyle='--', color='b', ms=5, mec='black',
                                   mew=2,
                                   markerfacecolor='black', fillstyle='full', picker=5)
        ax.add_line(newline)
        return fig, ax

    def test_within_tolerance(self):
        _, ax = self.create_test_plot()
        dx, dy = axis_lengths(ax)

        # The threshold of 0.01 gives a threshold distance of 0.0141421
        self.assertTrue(within_tolerance(0.005, dx, dy, 0.01))
        # The threshold of 0.05 gives a threshold distance of 0.0707106
        self.assertTrue(within_tolerance(0.05, dx, dy, 0.05))

    def test_outside_tolerance(self):
        _, ax = self.create_test_plot()
        dx, dy = axis_lengths(ax)
        # The threshold of 0.01 gives a threshold distance of 0.0141421
        self.assertFalse(within_tolerance(0.02, dx, dy, 0.01))
        # The threshold of 0.05 gives a threshold distance of 0.0707106
        self.assertFalse(within_tolerance(0.08, dx, dy, 0.05))

    def test_closest_value(self):
        xdata = np.arange(-10, 10, 1)
        ydata = [math.sin(x) for x in xdata]
        dx = abs(max(xdata) - min(xdata))
        dy = abs(max(ydata) - min(ydata))

        self.assertAlmostEqual(closest(0, 0, xdata, ydata, dx, dy)[0], 10)

        self.assertAlmostEqual(closest(4, 0.14, xdata, ydata, dx, dy)[0], 13)

        self.assertAlmostEqual(closest(3, 0, xdata, ydata, dx, dy)[0], 13)
