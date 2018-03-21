#!/usr/bin/env python3

import argparse
import numpy as np
import math
import segyio
import sys
import os
import json

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.lines import Line2D

from .utility import within_tolerance, axis_lengths, closest

def classes(cmap):
    definitions = [
        { 'name': '01', 'value': 1,  'hotkey': '1',      'hatch': '',   'color': cmap[0] },
        { 'name': '02', 'value': 2,  'hotkey': '2',      'hatch': '',   'color': cmap[1] },
        { 'name': '03', 'value': 3,  'hotkey': '3',      'hatch': '',   'color': cmap[2] },
        { 'name': '04', 'value': 4,  'hotkey': '4',      'hatch': '',   'color': cmap[3] },
        { 'name': '05', 'value': 5,  'hotkey': '5',      'hatch': '',   'color': cmap[4] },
        { 'name': '06', 'value': 6,  'hotkey': '6',      'hatch': '',   'color': cmap[5] },
        { 'name': '07', 'value': 7,  'hotkey': '7',      'hatch': '',   'color': cmap[6] },
        { 'name': '08', 'value': 8,  'hotkey': '8',      'hatch': '',   'color': cmap[7] },
        { 'name': '09', 'value': 9,  'hotkey': '9',      'hatch': '',   'color': cmap[8] },

        { 'name': '10', 'value': 10, 'hotkey': 'ctrl+1', 'hatch': 'xx', 'color': cmap[0] },
        { 'name': '12', 'value': 12, 'hotkey': 'ctrl+2', 'hatch': 'xx', 'color': cmap[1] },
        { 'name': '13', 'value': 13, 'hotkey': 'ctrl+3', 'hatch': 'xx', 'color': cmap[2] },
        { 'name': '14', 'value': 14, 'hotkey': 'ctrl+4', 'hatch': 'xx', 'color': cmap[3] },
        { 'name': '15', 'value': 15, 'hotkey': 'ctrl+5', 'hatch': 'xx', 'color': cmap[4] },
        { 'name': '16', 'value': 16, 'hotkey': 'ctrl+6', 'hatch': 'xx', 'color': cmap[5] },
        { 'name': '17', 'value': 17, 'hotkey': 'ctrl+7', 'hatch': 'xx', 'color': cmap[6] },
        { 'name': '18', 'value': 18, 'hotkey': 'ctrl+8', 'hatch': 'xx', 'color': cmap[7] },
        { 'name': '19', 'value': 19, 'hotkey': 'ctrl+9', 'hatch': 'xx', 'color': cmap[8] },

        { 'name': '20', 'value': 20, 'hotkey': 'alt+1',  'hatch': '++', 'color': cmap[0] },
        { 'name': '21', 'value': 21, 'hotkey': 'alt+2',  'hatch': '++', 'color': cmap[1] },
        { 'name': '22', 'value': 22, 'hotkey': 'alt+3',  'hatch': '++', 'color': cmap[2] },
        { 'name': '23', 'value': 23, 'hotkey': 'alt+4',  'hatch': '++', 'color': cmap[3] },
        { 'name': '24', 'value': 24, 'hotkey': 'alt+5',  'hatch': '++', 'color': cmap[4] },
        { 'name': '25', 'value': 25, 'hotkey': 'alt+6',  'hatch': '++', 'color': cmap[5] },
        { 'name': '26', 'value': 26, 'hotkey': 'alt+7',  'hatch': '++', 'color': cmap[6] },
        { 'name': '27', 'value': 27, 'hotkey': 'alt+8',  'hatch': '++', 'color': cmap[7] },
        { 'name': '28', 'value': 28, 'hotkey': 'alt+9',  'hatch': '++', 'color': cmap[8] },
    ]


    return definitions

def save_polys(fname, polys, x, y,  prefix = 'polys-'):
    poly_paths = []
    for poly,cls in polys.items():
        poly_paths.append({'vertices': poly.get_path().vertices.tolist(),
                       'poly_class': cls})

    polys_save={'x': x,
                'y': y,
                'poly_paths': poly_paths}

    fname = prefix + os.path.splitext(fname)[0] + '.json'
    output_path = os.path.join(os.getcwd(), fname)

    with open(output_path,'w') as f:
        json.dump(polys_save, f)

    print("Wrote", output_path)

def export(fname, output, prefix = 'labelmade-'):
    print("writing polygons to file")
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
    print("Wrote", output_path)

def mkoutput(polys, shape, xscale, yscale):
    traces, samples = shape
    output = np.zeros((traces, samples), dtype=np.single).T

    npoly = len(polys)
    for i, (poly, cls) in enumerate(polys.items(), 1):
        print('rendering polygon ({}/{})'.format(i, npoly))
        xys = poly.get_xy()

        # find the rectangle that covers all of the polygon
        w, n = xys.min(axis=0)
        e, s = xys.max(axis=0)

        w, n = int(math.floor(w)), int(math.floor(n))
        e, s = int(math.ceil(e + 1)), int(math.ceil(s + 1))

        w *= xscale
        e *= xscale
        s *= yscale
        n *= yscale

        xs = list(range(w, e))
        ys = list(range(n, s))
        xs1 = np.floor_divide(np.tile(xs, len(ys)), xscale)
        ys1 = np.floor_divide(np.repeat(ys, len(xs)), yscale)
        points = np.transpose([xs1, ys1])
        contains = poly.get_path().contains_points
        mask = contains(points)

        subout = output[n:s, w:e]
        np.place(subout, mask, [cls])

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
        self.saved_polys_path = args.load

        self.horizontal = args.horizontal
        self.vertical = args.vertical

        self.polys = {}
        self.last_removed = None
        self.pick = None
        self.current_poly_class = 1
        self.cmap = plt.get_cmap('tab10').colors[:9]

        self.keys = {'escape': self.clear,
                     'enter': self.mkpoly,
                     'ctrl+p': self.save_polys,
                     'd': self.rmpoly,
                     'u': self.undo,
                     'ctrl+e': self.export,
                     'z': self.undo_dot,
                     'ctrl+i': self.color_info,
                     'e': self.edit_poly
                     }

    def run(self):
        self.classes = classes(self.cmap)

        self.hotkeys = {d['hotkey']: d for d in self.classes}
        self.valclass = {d['value']: d for d in self.classes}

        self.fig, self.ax = plt.subplots()
        self.ax.imshow(self.traces[::self.horizontal, ::self.vertical].T,
                       aspect='auto',
                       cmap=plt.get_cmap(self.args.cmap))
        plt.subplots_adjust(bottom=0.2)

        self.line = Line2D(self.x, self.y, ls='--', c='#666666',
                      marker='x', mew=2, mec='#204a87', picker=5)
        self.ax.add_line(self.line)

        self.canvas = self.line.figure.canvas
        if self.overlaypath is None:
            self.canvas.mpl_connect('button_release_event', self.onrelease)
            self.canvas.mpl_connect('key_press_event', self.complete)
            self.canvas.mpl_connect('pick_event', self.onpick)

        if self.overlaypath is not None:
            self.add_overlay(self.overlaypath)

        if self.saved_polys_path is not None:
            self.load_polys(self.saved_polys_path)

        plt.show()

    def color_info(self,*_):
        with mpl.rc_context({'toolbar':'None'}):
            color_fig, color_ax = plt.subplots(figsize=(2,8))
            idx = 0
            modifiers = ['','ctrl+','alt+']
            for i in range(len(modifiers)):
                handles = plt.barh(np.arange(9), 1, left = i)
                for j, handle in enumerate(handles):
                    col = self.classes[idx]['color']
                    hatch = self.classes[idx]['hatch']
                    handle.set_facecolor(col)
                    handle.set_hatch(hatch)
                    idx+=1
            color_ax.set_ylabel('Corresponding color and texture per class')
            labels = [str(i+1) for i in range(9)]
            color_ax.set_yticklabels(labels)
            color_ax.set_yticks(np.arange(0,9))
            # It is possible to right/left/center align labels around ticks, but
            # it is not possible to align between ticks.. So remove major ticks
            # and add minor ticks inbetween with correct labels is a possibility
            # (in fact it is the suggested implementation in matplotlib documentation)
            color_ax.set_xticklabels('')
            ticks = [i+0.5 for i in range(len(modifiers))]
            color_ax.set_xticks(ticks, minor=True)
            color_ax.set_xticklabels(modifiers, minor=True)
            plt.tight_layout()
            color_fig.show()

    def save_polys(self, *_):
        save_polys(self.args.input, self.polys, self.args.horizontal, self.args.vertical)

    def load_polys(self, path):
        with open(path, 'r') as f:
            saved_polys = json.load(f)

        hori, vert = saved_polys['x'], saved_polys['y']

        if (self.horizontal != hori or self.vertical != vert):
            msg = """Warning: Could not load polys: horizontal downsampling from
            file (x={}) must equal current horizontal downsampling (x={}),
            vertical downsampling from file (y={}) must equal current vertical
            downsamping (y={})""".format(
            hori, self.horizontal, vert, self.vertical)
            print(msg)
            return

        for poly_path in saved_polys['poly_paths']:
            cls = self.valclass[poly_path['poly_class']]
            poly = patches.Polygon(poly_path['vertices'],
                                   alpha=0.5,
                                   fc=cls['color'],
                                   hatch=cls['hatch'])
            self.ax.add_patch(poly)
            self.polys[poly] = poly_path['poly_class']

    def add_overlay(self, path):
        with segyio.open(path) as f:
            traces = f.trace.raw[:]

        self.ax.imshow(traces[::self.horizontal, ::self.vertical].T,
                       aspect='auto',
                       cmap=plt.get_cmap(self.args.cmap),
                       alpha=0.5)

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
        if len(self.x) == 0: return
        cls = self.valclass[self.current_poly_class]

        poly = patches.Polygon(list(zip(self.x, self.y)),
                               alpha=0.5,
                               fc=cls['color'],
                               hatch=cls['hatch'])
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

    def edit_poly(self, event):
        if event.inaxes != self.line.axes: return

        if self.x!=[]:
            print("Complete current path before editing")
            return

        for poly, cls in self.polys.items():
            if not poly.contains(event)[0]: continue

            t = poly.get_path().vertices
            self.current_poly_class = cls
            self.x = t.T[0].tolist()[:-1]
            self.y = t.T[1].tolist()[:-1]
            self.line.set_data(self.x, self.y)

            poly.remove()
            self.polys.pop(poly)
            self.canvas.draw()
            break

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
        self.canvas.draw()

    def set_class(self, event):
        cls = self.hotkeys[event.key]
        self.current_poly_class = cls['value']

        # matplotlib uses numerical keys to set what axis has focus for zoom
        # and navigation emphasis. We always have one axis, and it should
        # always be navigatable
        self.ax.set_navigate(True)

        if event.inaxes != self.ax: return

        for poly in self.polys.keys():
            if not poly.contains(event)[0]: continue
            self.polys[poly] = cls['value']
            poly.set_facecolor(cls['color'])
            poly.set_hatch(cls['hatch'])

        self.canvas.draw()

    def complete(self, event):
        if event.key not in self.keys and event.key not in self.hotkeys: return

        if event.key in self.keys: self.keys[event.key](event)
        if event.key in self.hotkeys: self.set_class(event)
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
        data = mkoutput(self.polys, self.traces.shape, self.horizontal, self.vertical)
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

    parser.add_argument('-x',
                        '--horizontal',
                        '--downsample-horizontal',
                        type=int,
                        default=1,
                        help='Downsample horizontally (keep every n trace)')

    parser.add_argument('-y',
                        '--vertical',
                        '--downsample-vertical',
                        type=int,
                        default=1,
                        help='Downsample vertically (keep every n sample)')

    parser.add_argument('-l',
                        '--load',
                        type=str,
                        help='Filepath for saved polygons')

    args = parser.parse_args(args = argv[1:])

    with segyio.open(args.input) as f:
        traces = f.trace.raw[:]

    runner = plotter(args, traces)
    runner.run()

if __name__ == '__main__':
    main(sys.argv)
