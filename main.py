#! /usr/bin/env python3

import argparse
import math
import numpy as np
import segyio
import sys

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.lines import Line2D

class plotter(object):
    def __init__(self, fn):
        self.fn = fn
        self.x = []
        self.y = []
        self.fig = None
        self.canvas = None
        self.ax = None
        self.line = None

        self.polys = []
        self.last_removed = None
        self.pick = None
        self.current_poly_class = 0
        self.cmap = plt.get_cmap('tab10').colors

        self.keys = {'escape': self.clear,
                     'enter': self.mkpoly,
                     'd': self.rmpoly,
                     'u': self.undo,
                     'e': self.export
                     }

        [self.keys.update({str(key): self.set_class}) for key in range(1, 10, 1)]

        self.plot_segy()

    def plot_segy(self):
        with segyio.open(self.fn) as f:
            traces = f.trace.raw[:]

        self.fig, self.ax = plt.subplots()
        self.ax.imshow(traces, aspect='auto', cmap=plt.get_cmap('BuPu'))

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
        poly = patches.Polygon(list(zip(self.x, self.y)),
                               alpha=0.5,
                               fc=self.cmap[self.current_poly_class])
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
        # TODO: undo last added dot
        if self.last_removed is None: return
        if len(self.polys) > 0 and self.polys[-1] is self.last_removed: return
        self.polys.append(self.last_removed)
        self.ax.add_patch(self.last_removed)

    def set_class(self, event):
        for poly in self.polys:
            if not poly.contains(event)[0]: continue
            poly.set_facecolor(self.cmap[int(event.key)-1])

    def complete(self, event):
        if event.key not in self.keys: return

        self.keys[event.key](event)
        self.canvas.draw()

    def onpick(self, event):
        if event.artist is not self.line: return
        self.pick = 1

    def export(self, *_):
        with segyio.open(self.fn) as f:
            traces = f.raw[:]
            output = np.zeros(traces.shape, dtype=np.single)
            px, py = np.mgrid[0:traces.shape[0], 0:traces.shape[1]]
            points = np.c_[py.ravel(), px.ravel()]

            for poly in self.polys:
                mask = poly.get_path().contains_points(points)
                color = poly.get_facecolor()
                value = self.cmap.index((color[0], color[1], color[2]))+1
                np.place(output, mask, [value])

            meta = segyio.tools.metadata(f)
            with segyio.create('labelmade-' + self.fn, meta) as out:
                out.text[0] = f.text

                for i in range(1, 1 + f.ext_header):
                    out.text[i] = f.text[i]

                out.bin = f.bin
                out.header = f.header
                out.trace = output

def main(argv):
    parser = argparse.ArgumentParser(prog = argv[0],
                                     description='Label those slices yo')
    parser.add_argument('input', type=str, help='input file')
    args = parser.parse_args(args = argv[1:])

    plotter(args.input)

if __name__ == '__main__':
    main(sys.argv)
