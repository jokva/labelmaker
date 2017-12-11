#! /usr/bin/env python3

import argparse
import numpy as np
import segyio
import sys

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.lines import Line2D
from utility import within_tolerance, closest, axis_lengths

def export(fname, polys, prefix = 'labelmade-'):
    with segyio.open(fname) as f:
        traces, samples = len(f.trace), len(f.trace[0])
        output = np.zeros(shape, dtype=np.single)
        px, py = np.mgrid[0:traces, 0:samples]
        points = np.c_[py.ravel(), px.ravel()]

        for poly in polys:
            mask = poly.get_path().contains_points(points)
            np.place(output, mask, [1])

        meta = segyio.tools.metadata(f)
        with segyio.create(prefix + fname, meta) as out:
            out.text[0] = f.text[0]

            for i in range(1, 1 + f.ext_headers):
                out.text[i] = f.text[i]

            out.bin = f.bin
            out.header = f.header
            out.trace = output

class plotter(object):
    def __init__(self, args, traces):
        self.args = args
        self.x = []
        self.y = []
        self.fig = None
        self.canvas = None
        self.ax = None
        self.line = None
        self.threshold = args.threshold
        self.traces = traces

        self.polys = []
        self.last_removed = None
        self.pick = None

        self.keys = {'escape': self.clear,
                     'enter': self.mkpoly,
                     'd': self.rmpoly,
                     'u': self.undo,
                     'e': self.export
                     }
    def run(self):
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(self.traces, aspect='auto', cmap=plt.get_cmap('BuPu'))

        self.line = Line2D(self.x, self.y, ls='--', c='#666666',
                      marker='x', mew=2, mec='#204a87', picker=5)
        self.ax.add_line(self.line)

        self.canvas = self.line.figure.canvas
        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('key_press_event', self.complete)
        self.canvas.mpl_connect('pick_event', self.onpick)

        plt.show()

    def onrelease(self, event):
        if self.pick is not None:
            if self.current_point:
                self.move_point(event.xdata, event.ydata)
            self.pick = None
            return

        if self.canvas.manager.toolbar._active is not None: return
        if event.inaxes != self.line.axes: return
        if event.button != 1: return

        self.x.append(event.xdata)
        self.y.append(event.ydata)

        self.line.set_data(self.x, self.y)
        self.canvas.draw()

    def clear(self, *_):
        self.x, self.y = [], []
        self.line.set_data(self.x, self.y)

    def mkpoly(self, *_):
        poly = patches.Polygon(list(zip(self.x, self.y)), alpha = 0.5)
        self.ax.add_patch(poly)

        self.polys.append(poly)
        self.clear()

    def rmpoly(self, event):
        if event.inaxes != self.line.axes: return

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

        self.line.set_data(self.x, self.y)
        self.canvas.draw()

    def complete(self, event):
        if event.key not in self.keys: return

        self.keys[event.key](event)
        self.canvas.draw()

    def onpick(self, event):
        if event.artist is not self.line: return
        self.pick = 1
        xp, yp = event.mouseevent.xdata, event.mouseevent.ydata
        xdata, ydata = self.line.get_data()

        dx, dy = axis_lengths(self.line.axes)
        idx, distance = closest(xp, yp, xdata, ydata, dx, dy)

        if within_tolerance(distance, dx, dy, self.threshold):
            self.current_point = (xdata[idx], ydata[idx], idx)

    def move_point(self, xp, yp):
        _, _, idx = self.current_point

        self.x[idx] = xp
        self.y[idx] = yp

        self.line.set_data(self.x, self.y)
        self.canvas.draw()
        self.current_point = None

    def export(self, *_):
        export(self.args.input, self.polys, prefix = self.args.prefix)

def main(argv):
    parser = argparse.ArgumentParser(prog = argv[0],
                                     description='Label those slices yo')
    parser.add_argument('input', type=str,
                                 help='input file')
    parser.add_argument('--threshold', type=float,
                                       help='point selection sensitivity',
                                       default = 0.01)
    args = parser.parse_args(args = argv[1:])

    with segyio.open(args.input) as f:
        traces = f.trace.raw[:]

    runner = plotter(args, traces)
    runner.run()

if __name__ == '__main__':
    main(sys.argv)
