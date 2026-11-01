"""Drawing engines: "layers", "exact", "strokes"."""

import numpy as np

from itd.banner.jit import jit


@jit
def to_arrays(op_color, op_start, out_pts):
    """Typed lists of an engine run -> numpy arrays (color index per op, op starts, points)."""
    n = len(op_color)
    colors = np.empty(n, dtype=np.int64)
    for k in range(n):
        colors[k] = op_color[k]
    starts = np.empty(len(op_start), dtype=np.int64)
    for k in range(len(op_start)):
        starts[k] = op_start[k]
    pts = np.empty((len(out_pts), 2))
    for k in range(len(out_pts)):
        pts[k, 0] = out_pts[k][0]
        pts[k, 1] = out_pts[k][1]
    return colors, starts, pts


@jit
def widths_array(op_width):
    out = np.empty(len(op_width))
    for k in range(len(op_width)):
        out[k] = op_width[k]
    return out
