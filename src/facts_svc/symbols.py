"""Reusable engineering symbols, including actual antiparallel SCR paths.

SCR geometry is adapted from the author's rectifier_art.py, including the
optional extraction of schemdraw.elements.SCR segments and its compatible
fallback.  The fallback keeps SVG export usable with zero dependencies.
"""

from __future__ import annotations

import math
from functools import lru_cache
from xml.etree import ElementTree as ET

from .svg import SVGCanvas, node


@lru_cache(maxsize=1)
def scr_segments() -> tuple[tuple[str, tuple[tuple[float, float], ...]], ...]:
    """Read Schemdraw's SCR segments when present, else use equivalent paths."""
    try:
        from schemdraw import elements as elm
    except ImportError:
        elm = None

    if elm is not None:
        native = elm.SCR()
        segments: list[tuple[str, tuple[tuple[float, float], ...]]] = []
        for segment in native.segments:
            if hasattr(segment, "path"):
                segments.append(("polyline", tuple((float(x), float(y)) for x, y in segment.path)))
            elif hasattr(segment, "verts"):
                segments.append(("polygon", tuple((float(x), float(y)) for x, y in segment.verts)))
            else:
                raise ValueError("Unexpected Schemdraw SCR segment")
        if len(segments) != 3:
            raise ValueError("Unexpected Schemdraw SCR geometry")
        return tuple(segments)

    nan = math.nan
    return (
        ("polyline", ((0, 0), (nan, nan), (.35, .25), (.35, -.25), (nan, nan), (.35, 0))),
        ("polygon", ((0, .25), (.35, 0), (0, -.25))),
        ("polyline", ((.35, 0), (.65, -.3), (.65, -.5))),
    )


class ElectricalSymbols:
    """Place consistent electrical components at exact terminal coordinates."""

    def __init__(self, canvas: SVGCanvas):
        self.c = canvas

    def terminal(self, parent: ET.Element, x: float, y: float) -> None:
        self.c.circle(parent, x, y, 5.1, fill=self.c.theme.ink,
                      stroke=self.c.theme.ink, stroke_width=1)

    def inductor(self, parent: ET.Element, x: float, top: float, bottom: float,
                 label: str) -> None:
        """Draw a vertical coil with conductive endpoints at top and bottom."""
        if bottom - top < 93:
            raise ValueError("Inductor needs at least 93 SVG coordinate units")
        c, ink = self.c, self.c.theme.reactor
        g = c.group(parent, f"inductor-{label}", data_device="inductor")
        start = top + 8
        c.line(g, x, top, x, start, color=ink)
        cmd = f"M {x},{start}"
        for k in range(4):
            y = start + 19*k
            cmd += f" C {x-20},{y+2} {x-20},{y+17} {x},{y+19}"
        c.path(g, cmd, color=ink)
        c.line(g, x, start+4*19, x, bottom, color=ink)
        c.math(g, x+39, (top+bottom)/2+6, [("L", "variable"),
                                            (label, "subscript-roman")],
               color=ink, size=19)

    def capacitor(self, parent: ET.Element, x: float, top: float,
                  bottom: float, label: str) -> None:
        """Capacitor plates are electrically separated by a visible gap."""
        if bottom - top < 36:
            raise ValueError("Capacitor needs at least 36 SVG coordinate units")
        c, ink = self.c, self.c.theme.capacitor
        g = c.group(parent, f"capacitor-{label}", data_device="capacitor")
        middle = (top + bottom)/2
        c.line(g, x, top, x, middle-10, color=ink)
        c.line(g, x-26, middle-10, x+26, middle-10, color=ink)
        c.line(g, x-26, middle+10, x+26, middle+10, color=ink)
        c.line(g, x, middle+10, x, bottom, color=ink)
        c.math(g, x+38, middle+7, [("C", "variable"),
                                   (label, "subscript-roman")],
               color=ink, size=19)

    def scr(self, parent: ET.Element, x: float, cy: float, *,
            direction: str, name: str, label: str | None = None,
            scale: float = 88) -> tuple[float, float]:
        """Draw one SCR, returning its upper and lower terminal y coordinates.

        ``down`` means anode above cathode; ``up`` means cathode above
        anode.  The gate lead always stays outside the two-valve stack.
        """
        if direction not in {"down", "up"}:
            raise ValueError("SCR direction must be 'down' or 'up'")
        c = self.c
        sign = 1 if direction == "down" else -1
        g = c.group(parent, f"scr-{name}", data_device="SCR",
                    data_direction=direction, data_name=name)
        color = c.theme.accent

        def xy(p: tuple[float, float]) -> tuple[float, float]:
            return (x + sign * scale * p[1], cy + sign * scale * (p[0]-.175))

        for kind, points in scr_segments():
            if kind == "polygon":
                mapped = [xy(p) for p in points]
                node(g, "polygon", points=" ".join(f"{px:.3f},{py:.3f}" for px, py in mapped),
                     fill=c.theme.paper, stroke=color, stroke_width=3.2,
                     stroke_linejoin="round")
                continue
            runs: list[list[tuple[float, float]]] = [[]]
            for p in points:
                if not all(math.isfinite(t) for t in p):
                    runs.append([])
                else:
                    runs[-1].append(xy(p))
            for run in runs:
                if len(run) >= 2:
                    c.polyline(g, run, color=color, width=3.2)
        label_x = x-29 if direction == "down" else x+29
        c.math(g, label_x, cy-22, [("T", "variable"),
                                    (label or name, "subscript-roman")],
               color=color, size=18,
               anchor="end" if direction == "down" else "start")
        return cy-.175*scale, cy+.175*scale

    def antiparallel_valve(self, parent: ET.Element, x: float, top: float,
                           bottom: float, *, device_id: str) -> None:
        """Two opposed SCR branches connected only at their common end nodes."""
        c = self.c
        if bottom-top < 115:
            raise ValueError("Insufficient space for antiparallel SCR pair")
        g = c.group(parent, f"valve-{device_id}", data_device="antiparallel-valve")
        span, cy = 44, (top+bottom)/2
        left, right = x-span, x+span
        # A shared vertical central conductor would short-circuit both SCRs.
        c.line(g, left, top, right, top)
        c.line(g, left, bottom, right, bottom)
        for xpos, direction, number in ((left, "down", "1"),
                                         (right, "up", "2")):
            y_hi, y_lo = self.scr(g, xpos, cy, direction=direction,
                                   name=f"{device_id}{number}",
                                   label=number)
            c.line(g, xpos, top, xpos, y_hi)
            c.line(g, xpos, y_lo, xpos, bottom)
        c.line(g, x, top-18, x, top)
        c.line(g, x, bottom, x, bottom+18)
        self.terminal(g, x, top)
        self.terminal(g, x, bottom)

    def transformer(self, parent: ET.Element, x: float, grid_bus: float,
                    svc_bus: float) -> None:
        """Conventional stacked two-winding single-line transformer symbol."""
        c, ink = self.c, self.c.theme.ink
        g = c.group(parent, "coupling-transformer", data_device="transformer")
        r, y1, y2 = 28, 235, 282
        c.line(g, x, grid_bus, x, y1-r)
        c.circle(g, x, y1, r, fill="none", stroke=ink)
        c.circle(g, x, y2, r, fill="none", stroke=ink)
        c.line(g, x, y2+r, x, svc_bus)
        c.text(g, x+42, 250, "Coupling", size=15, color=c.theme.muted)
        c.text(g, x+42, 270, "transformer", size=15, color=c.theme.muted)

    def ground(self, parent: ET.Element, x: float, top: float) -> None:
        c = self.c
        g = c.group(parent, "symbolic-return", data_device="ground")
        c.line(g, x, top, x, top+21)
        for dy, half in ((22, 23), (30, 15), (38, 7)):
            c.line(g, x-half, top+dy, x+half, top+dy, width=2.7)
