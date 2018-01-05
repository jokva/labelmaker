#!/usr/bin/env python3

import argparse
import numpy as np
import segyio
import sys
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.lines import Line2D

from .utility import within_tolerance, axis_lengths, closest

def export(fname, output, prefix = 'labelmade-'):
    with segyio.open(fname) as f:
        meta = segyio.tools.metadata(f)
        output_path = os.path.join(os.getcwd(), prefix + os.path.basename(fname))
        with segyio.create(output_path, meta) as out:
            out.text[0] = f.text[0]

            for i in range(1, 1 + f.ext_headers):
                out.text[i] = f.text[i]

            out.bin = f.bin
            out.header = f.header
            out.trace = output
    print("Wrote", prefix + fname)

def mkoutput(polys, shape):
    traces, samples = shape
    output = np.zeros((traces, samples), dtype=np.single).T
    px, py = np.mgrid[0:samples, 0:traces]
    points = np.c_[py.ravel(), px.ravel()]

    for poly, cls in polys.items():
        mask = poly.get_path().contains_points(points)
        value = cls
        np.place(output, mask, [value])
    return output.T

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
        self.overlaypath = args.compare
        self.xlim = None
        self.ylim = None
        self.xlim_orig = None
        self.ylim_orig = None
        self.background = None

        self.polys = {}
        self.last_removed = None
        self.pick = None
        self.current_poly_class = 1
        self.cmap = plt.get_cmap('tab10').colors

        self.keys = {'escape': self.clear,
                     'enter': self.mkpoly,
                     'd': self.rmpoly,
                     'u': self.undo,
                     'e': self.export,
                     'z': self.undo_dot,
                     'h': self.original_view
                     }

        for key in range(1,10):
            self.keys[str(key)] = self.set_class

    def run(self):

        self.fig, self.ax = plt.subplots()
        self.ax.imshow(self.traces.T, aspect='auto', cmap=plt.get_cmap(self.args.cmap))
        self.fig.canvas.draw()
        self.xlim, self.ylim = self.ax.get_xlim(), self.ax.get_ylim()
        self.xlim_orig, self.ylim_orig = self.ax.get_xlim(), self.ax.get_ylim()
        self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)

        self.line = Line2D(self.x, self.y, ls='--', c='#666666',
                      marker='x', mew=2, mec='#204a87', picker=5)
        self.ax.add_line(self.line)

        self.canvas = self.line.figure.canvas
        if self.overlaypath is None:
            self.canvas.mpl_connect('button_release_event', self.onrelease)
            self.canvas.mpl_connect('key_press_event', self.complete)
            self.canvas.mpl_connect('pick_event', self.onpick)
            self.canvas.mpl_connect('resize_event', self.onresize)

        if self.overlaypath is not None:
            self.add_overlay(self.overlaypath)

        plt.show()

    def add_overlay(self, path):
        with segyio.open(path) as f:
            traces = f.trace.raw[:]

        self.ax.imshow(traces.T, aspect='auto', cmap=plt.get_cmap(self.args.cmap), alpha=0.5)

    def visible(self, x):
        self.line.set_visible(x)
        for poly in self.polys.keys():
            poly.set_visible(x)

    def update_background(self):
        self.xlim, self.ylim = self.ax.get_xlim(), self.ax.get_ylim()
        self.ax.clear()

        self.ax.imshow(self.traces.T, aspect='auto', cmap=plt.get_cmap(self.args.cmap))
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.fig.canvas.draw()

        self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self.blit()

    def onresize(self, *_):
        self.update_background()

    def original_view(self, *_):
        self.ax.set_xlim(self.xlim_orig)
        self.ax.set_ylim(self.ylim_orig)
        self.update_background()

    def blit(self):
        self.fig.canvas.restore_region(self.background)
        self.ax.draw_artist(self.line)

        for poly in self.polys.keys():
            self.ax.draw_artist(poly)

        self.fig.canvas.blit(self.ax.bbox)
        self.fig.canvas.flush_events()

    def onrelease(self, event):
        tool_mode = plt.get_current_fig_manager().toolbar.mode
        if tool_mode == "zoom rect" or tool_mode == "pan/zoom":
            self.update_background()
            return

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
        self.blit()

    def clear(self, *_):
        self.x, self.y = [], []
        self.line.set_data(self.x, self.y)
        self.canvas.draw()

    def mkpoly(self, *_):
        if len(self.x) < 3: return

        poly = patches.Polygon(list(zip(self.x, self.y)),
                               alpha=0.5,
                               fc=self.cmap[self.current_poly_class-1])
        self.ax.add_patch(poly)

        self.polys[poly] = self.current_poly_class
        self.clear()

    def rmpoly(self, event):
        if event.inaxes != self.line.axes: return

        for poly in self.polys:
            if not poly.contains(event)[0]: continue
            poly.remove()
            self.last_removed = (poly, self.polys.pop(poly))
            return

    def undo(self, *_ ):
        if self.last_removed is None: return
        if self.last_removed[0] in self.polys: return
        self.polys.update([self.last_removed])
        self.ax.add_patch(self.last_removed[0])

    def undo_dot(self, *_):
        if len(self.x) == 0: return
        self.x.pop()
        self.y.pop()
        self.line.set_data(self.x, self.y)

    def set_class(self, event):
        cls = int(event.key)
        self.current_poly_class = cls

        # matplotlib uses numerical keys to set what axis has focus for zoom
        # and navigation emphasis. We always have one axis, and it should
        # always be navigatable
        self.ax.set_navigate(True)

        if event.inaxes != self.ax: return

        for poly in self.polys.keys():
            if not poly.contains(event)[0]: continue
            self.polys[poly] = cls
            poly.set_facecolor(self.cmap[cls-1])

    def complete(self, event):
        if event.key not in self.keys: return

        self.keys[event.key](event)
        self.blit()

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
        self.current_point = None

    def export(self, *_):
        data = mkoutput(self.polys, self.traces.shape)
        export(self.args.input, data, prefix = self.args.prefix)

def main(argv = None):
    if argv is None: argv = sys.argv

    parser = argparse.ArgumentParser(prog = argv[0],
                                     description='Labelmaker - open segyiofile, '
                                                 'mark areas interactively and export the result')
    parser.add_argument('input',
                        type=str,
                        help='Input file')

    parser.add_argument('-t',
                        '--threshold',
                        type=float,
                        help='Point selection sensitivity',
                        default=0.01)

    parser.add_argument('-p',
                        '--prefix',
                        type=str,
                        help='Output file prefix',
                        default='labelmade-')

    parser.add_argument('-d',
                        '--compare',
                        type=str,
                        help='Filepath to exported results (for comparing)')

    parser.add_argument('-c',
                        '--cmap',
                        '--colours',
                        type=str,
                        default='seismic',
                        help='Set colour map')

    args = parser.parse_args(args = argv[1:])

    with segyio.open(args.input) as f:
        traces = f.trace.raw[:]

    runner = plotter(args, traces)
    runner.run()

if __name__ == '__main__':
    main(sys.argv)
