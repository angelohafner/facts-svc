"""SVC schematic composer, isolated from models and symbol geometry."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from .model import Branch, BranchKind, SVCConfig
from .svg import SVGCanvas
from .symbols import ElectricalSymbols


class SVCRenderer:
    """Render topologically consistent, editable SVG SVC diagrams.

    The output is a conceptual single-line/per-phase equivalent.  It does not
    specify delta/wye winding configurations or predict instantaneous currents.
    """

    HEIGHT = 1020
    GRID_Y = 170
    BUS_Y = 355
    RETURN_Y = 815
    STEP = 270

    def __init__(self, config: SVCConfig):
        self.config = config
        self.width = max(1060, 260+len(config.branches)*self.STEP)
        self.canvas = SVGCanvas(self.width, self.HEIGHT)
        self.symbols = ElectricalSymbols(self.canvas)

    def _positions(self) -> list[float]:
        count = len(self.config.branches)
        span = (count-1)*self.STEP
        first = self.width/2-span/2
        return [first+i*self.STEP for i in range(count)]

    def _background(self) -> None:
        c = self.canvas
        g = c.layer("Background", "background")
        c.rect(g, 0, 0, self.width, self.HEIGHT, fill=c.theme.canvas)
        c.rect(g, 24, 22, self.width-48, self.HEIGHT-44,
               fill=c.theme.paper, radius=18, stroke=c.theme.border)

    def _header(self) -> None:
        c, t = self.canvas, self.canvas.theme
        g = c.layer("Titles and legend", "titles")
        c.text(g, 65, 74, self.config.title, size=30, bold=True)
        c.text(g, 65, 109, "Static VAR compensator  |  functional electrical diagram",
               size=17, color=t.muted)
        c.line(g, 65, 130, self.width-65, 130, color=t.border, width=2)
        c.text(g, 90, 153, "PCC / AC GRID", size=15, bold=True, color=t.muted)
        c.text(g, 90, 338, "SVC BUS", size=15, bold=True, color=t.muted)
        c.text(g, 85, 858, "Symbolic return (phase-equivalent representation)",
               size=15, color=t.muted)
        c.line(g, 66, 888, self.width-66, 888, color=t.border, width=2)
        c.text(g, 85, 921,
               "TCR: phase-angle control   |   TSC / TSR: switched steps   |   FC: fixed capacitor   |   FILTER: tuned LC branch",
               color=t.muted, size=15)
        c.text(g, 85, 949,
               "Conceptual single-line/per-phase diagram. Actual three-phase delta/wye connections and ratings are not specified.",
               color=t.muted, size=15)
        c.math(g, 85, 978, [("TCR firing range: ", "roman"),
                            ("90", "roman"), ("°", "unit"),
                            (" ≤ ", "roman"), ("α", "variable"),
                            (" ≤ ", "roman"), ("180", "roman"),
                            ("°", "unit"),
                            ("   |   Conceptual only, not an EMT simulation.", "roman")],
               color=t.muted, size=15)

    def _buses(self, positions: list[float]) -> None:
        c = self.canvas
        g = c.layer("Grid, transformer and buses", "buses")
        center = self.width/2
        # The PCC bus and secondary bus are separated by a transformer symbol.
        c.line(g, center-320, self.GRID_Y, center+320, self.GRID_Y, width=5.0)
        c.circle(g, center-320, self.GRID_Y, 6, fill=c.theme.ink)
        c.circle(g, center+320, self.GRID_Y, 6, fill=c.theme.ink)
        if self.config.transformer:
            self.symbols.transformer(g, center, self.GRID_Y, self.BUS_Y)
        else:
            c.line(g, center, self.GRID_Y, center, self.BUS_Y)
            c.text(g, center+24, 263, "Direct connection", size=15,
                   color=c.theme.muted)
        left, right = positions[0]-99, positions[-1]+99
        c.line(g, left, self.BUS_Y, right, self.BUS_Y, width=5.4)
        c.line(g, left, self.RETURN_Y, right, self.RETURN_Y, width=4.0)
        for x in positions:
            self.symbols.terminal(g, x, self.BUS_Y)
            self.symbols.terminal(g, x, self.RETURN_Y)
        # Only the single-line/per-phase equivalent uses this return symbol.
        self.symbols.ground(g, center, self.RETURN_Y)

    @staticmethod
    def _device_index(branch: Branch) -> str:
        """Derive an editable device index from the branch's numeric suffix."""
        digits = "".join(ch for ch in branch.name if ch.isdigit())
        return digits or "1"

    def _draw_branch(self, parent: ET.Element, branch: Branch, x: float) -> None:
        c, s = self.canvas, self.symbols
        kind = branch.kind
        ident = self._device_index(branch)
        gid = "branch-" + "".join(ch.lower() if ch.isalnum() else "-"
                                         for ch in branch.name).strip("-")
        group = c.group(parent, gid, data_kind=kind.value, data_name=branch.name)
        c.text(group, x+24, 395, branch.name, size=18, bold=True)
        if kind in (BranchKind.TCR, BranchKind.TSR):
            c.line(group, x, self.BUS_Y, x, 440)
            s.inductor(group, x, 440, 537, ident)
            c.line(group, x, 537, x, 557)
            s.antiparallel_valve(group, x, 575, 713,
                                 device_id=f"{kind.value}{ident}-")
            c.line(group, x, 731, x, self.RETURN_Y)

        elif kind is BranchKind.TSC:
            c.line(group, x, self.BUS_Y, x, 419)
            s.inductor(group, x, 419, 512, ident)
            c.line(group, x, 512, x, 527)
            s.capacitor(group, x, 527, 580, ident)
            c.line(group, x, 580, x, 601)
            s.antiparallel_valve(group, x, 619, 745,
                                 device_id=f"TSC{ident}-")
            c.line(group, x, 763, x, self.RETURN_Y)
        elif kind is BranchKind.FC:
            c.line(group, x, self.BUS_Y, x, 488)
            s.capacitor(group, x, 488, 553, ident)
            c.line(group, x, 553, x, self.RETURN_Y)
        elif kind is BranchKind.FILTER:
            c.line(group, x, self.BUS_Y, x, 424)
            s.inductor(group, x, 424, 521, f"F{branch.harmonic_order}")
            c.line(group, x, 521, x, 563)
            s.capacitor(group, x, 563, 625, f"F{branch.harmonic_order}")
            c.line(group, x, 625, x, self.RETURN_Y)
        else:
            raise AssertionError(f"Unhandled SVC branch kind: {kind}")

    def render(self) -> SVGCanvas:
        """Create the SVG canvas.  Do not call twice on one renderer instance."""
        if len(self.canvas.root):
            raise RuntimeError("Each SVCRenderer instance can only render once")
        self.canvas.metadata(self.config.title,
                             "Conceptual SVC shunt circuit. TCR and TSC branches "
                             "show individual antiparallel SCRs; connections are "
                             "a single-line/per-phase equivalent, not a simulation.")
        self._background()
        self._header()
        positions = self._positions()
        self._buses(positions)
        branches = self.canvas.layer("SVC branches", "branches")
        for x, branch in zip(positions, self.config.branches):
            self._draw_branch(branches, branch, x)
        return self.canvas

    def save(self, path: str | Path) -> Path:
        return self.render().save(path)


def render_svg(config: SVCConfig, path: str | Path) -> Path:
    """Convenience function for scripts and downstream FACTS projects."""
    return SVCRenderer(config).save(path)
