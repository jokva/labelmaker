# Labelmaker #

The Labelmaker tool provides a method to categorize layers in seismic data.
The tool uses segyio to read seismic data and Matplotlib to produce the
graphical overview to the user.

The user draws an area (polygon) containing the layer at hand and selects
the type.

### Command line arguments:

```-d``` or ```--compare```:   Specify overlay results. Previously exported segy results
                      from the labelmaker may be added with this argument.
                      In such case the results will overlay the inputfile and
                      it will not be possible to create new polygons.

```-t``` or ```--threshold```: Set point selection sensitivity. The setting impacts the
                      radius when selecting points to move. Default: 0.01.

```-p``` or ```--prefix```:     File path prefix for exported results.
                      Default:'Labelmade-'.

Mouse shortcuts:

```<Left Mousebutton>``` Creates a point in the plot. Further addition of points
                   creates a line between the points.

### Keyboard shortcuts:

```<enter>```  Draws a polygon based on the points selected by the user. Also resets
         the points in the line, such that the next point created by clicking
         the mousebutton starts on a new line.

```<escape>``` Clear drawn points.

```<z>```      Undo last created point.

```<d>```     Removes the polygon which the cursor currently hovers. This action
         will do nothing if the cursor is not hovering a polygon.

```<u>```      Undo deletion of last polygon. This action will only add the latest
         removed polygon.

```<h>```      Restore to original view.

```<m>```      Restore last view (if the view has been zoomed, restores the
previous view)

```<i>```      Refresh view. In any case polygons or lines are not updating,
it is possible to refresh the view.

```<e>```      Export the results. The Labelmaker creates a new segy file with the
         same headers, text content and dimensions as the input file. The segy
         file contains 0-values for all coordinates outside of any drawn
         polygon. Depending on the type chosen by the user, the coordinates
         within polygons will have values from 1 to n.
