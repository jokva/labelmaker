#! /usr/bin/env python3

import argparse
import numpy as np
import segyio
import sys

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib import patches
from matplotlib.lines import Line2D
from utility import within_tolerance, closest, axis_lengths

class polybuilder(object):
    def __init__(self, control, ax, threshold):
        self.x = list(control.get_xdata())
        self.y = list(control.get_ydata())
        self.canvas = control.figure.canvas
        self.control = control
        self.ax = ax
        self.threshold = threshold
        self.current_point = None

        self.polys = []
        self.last_removed = None
        self.pick = None

        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('key_press_event', self.complete)
        self.canvas.mpl_connect('pick_event', self.onpick)

        self.keys = {   'escape': self.clear,
                        'enter': self.mkpoly,
                        'd': self.rmpoly,
                        'u': self.undo,
                        'z': self.undo_dot
                    }

    def onrelease(self, event):
        if self.pick is not None:
            if self.current_point:
                self.move_point(event.xdata, event.ydata)
            self.pick = None
            return

        if self.canvas.manager.toolbar._active is not None: return
        if event.inaxes != self.control.axes: return
        if event.button != 1: return

        self.x.append(event.xdata)
        self.y.append(event.ydata)

        self.control.set_data(self.x, self.y)
        self.canvas.draw()

    def clear(self, *_):
        self.x, self.y = [], []
        self.control.set_data(self.x, self.y)

    def mkpoly(self, *_):
        poly = patches.Polygon(list(zip(self.x, self.y)), alpha = 0.5)
        self.ax.add_patch(poly)

        self.polys.append(poly)
        self.clear()

    def rmpoly(self, event):
        if event.inaxes != self.control.axes: return

        for poly in self.polys:
            if not poly.contains(event)[0]: continue
            poly.remove()
            self.last_removed = poly
            self.polys.remove(poly)

    def undo(self, *_ ):
        if self.last_removed is None: return
        if len(self.polys) > 0 and self.polys[-1] is self.last_removed: return
        self.polys.append(self.last_removed)
        self.ax.add_patch(self.last_removed)

    def undo_dot(self, *_):
        if len(self.x) == 0: return
        self.x.pop()
        self.y.pop()

        self.control.set_data(self.x, self.y)
        self.canvas.draw()

    def complete(self, event):
        if event.key not in self.keys: return

        self.keys[event.key](event)
        self.canvas.draw()

    def onpick(self, event):
        if event.artist is not self.control: return
        self.pick = 1
        xp, yp = event.mouseevent.xdata, event.mouseevent.ydata
        xdata, ydata = self.control.get_data()

        dx, dy = axis_lengths(self.control.axes)
        idx, distance = closest(xp, yp, xdata, ydata, dx, dy)

        if within_tolerance(distance, dx, dy, self.threshold):
            self.current_point = (xdata[idx], ydata[idx], idx)

    def move_point(self, xp, yp):
        _, _, idx = self.current_point

        self.x[idx] = xp
        self.y[idx] = yp

        self.control.set_data(self.x, self.y)
        self.canvas.draw()
        self.current_point = None

def main(argv):
    parser = argparse.ArgumentParser(prog = argv[0],
                                     description='Label those slices yo')
    parser.add_argument('input', type=str, help='input file')
    args = parser.parse_args(args = argv[1:])

    with segyio.open(args.input) as f:
        traces = f.trace.raw[:]
        low, high = np.nanmin(traces), np.nanmax(traces)

        _, ax = plt.subplots()
        ax.imshow(traces, aspect='auto', cmap = plt.get_cmap('BuPu'))

        line = Line2D([], [], ls='--', c='#666666',
                      marker='x', mew=2, mec='#204a87', picker = 5)
        ax.add_line(line)
        pb = polybuilder(line, ax, threshold=0.01)

        plt.show()

if __name__ == '__main__':
    main(sys.argv)
