"""Topology and SVG checks for structural SVC diagram correctness."""

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from facts_svc import Branch, BranchKind, ElectricalSymbols, SVCConfig, SVCRenderer, SVGCanvas, presets, render_svg

SVG = "{http://www.w3.org/2000/svg}"


class RendererTests(unittest.TestCase):
    def test_each_preset_renders_parseable_svg(self):
        for name, config in presets().items():
            with self.subTest(name=name):
                canvas = SVCRenderer(config).render()
                root = ET.fromstring(canvas.as_svg_bytes())
                self.assertTrue(root.tag.endswith("svg"))
                self.assertEqual(len(root.findall(f".//{SVG}g[@data-kind]")), len(config.branches))
                self.assertEqual(len(root.findall(f".//{SVG}g[@data-device='antiparallel-valve']")),
                                 sum(b.kind in (BranchKind.TCR, BranchKind.TSR, BranchKind.TSC) for b in config.branches))
                self.assertEqual(len(root.findall(f".//{SVG}g[@data-device='SCR']")),
                                 2*sum(b.kind in (BranchKind.TCR, BranchKind.TSR, BranchKind.TSC) for b in config.branches))
                self.assertEqual(len(root.findall(f".//{SVG}g[@data-device='ground']")), 1)

    def test_antiparallel_scr_are_opposite_direction(self):
        root = ET.fromstring(SVCRenderer(presets()["tsc-tcr"]).render().as_svg_bytes())
        for valve in root.findall(f".//{SVG}g[@data-device='antiparallel-valve']"):
            directions = [item.get("data-direction") for item in valve.findall(f".//{SVG}g[@data-device='SCR']")]
            self.assertEqual(directions, ["down", "up"])

    def test_anti_parallel_pair_has_no_central_short(self):
        c = SVGCanvas(200, 250)
        ElectricalSymbols(c).antiparallel_valve(c.root, 100, 30, 190, device_id="X-")
        root = ET.fromstring(c.as_svg_bytes())
        valve = root.find(f".//{SVG}g[@data-device='antiparallel-valve']")
        self.assertIsNotNone(valve)
        # There must be no wire joining the upper and lower nodes on x=100.
        for line in valve.findall(f".//{SVG}line"):
            self.assertFalse(line.get("x1") == line.get("x2") == "100"
                             and float(line.get("y1")) <= 30
                             and float(line.get("y2")) >= 190)

    def test_no_transformer_and_filename_creation(self):
        from dataclasses import replace
        config = replace(presets()["fc-tcr"], transformer=False)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/"sub"/"figure.svg"
            render_svg(config, output)
            root = ET.parse(output).getroot()
            self.assertFalse(root.findall(f".//{SVG}g[@data-device='transformer']"))
            self.assertTrue(root.findall(f".//{SVG}g[@data-device='capacitor']"))

    def test_font_roles_for_variables_and_units(self):
        canvas = SVCRenderer(presets()["tcr-only"]).render()
        root = ET.fromstring(canvas.as_svg_bytes())
        var = root.findall(f".//{SVG}tspan[@data-math-role='variable']")
        unit = root.findall(f".//{SVG}tspan[@data-math-role='unit']")
        self.assertTrue(any(t.text == "α" and t.get("font-style") == "italic" for t in var))
        self.assertTrue(any(t.text == "°" and t.get("font-style") == "normal" for t in unit))


if __name__ == "__main__":
    unittest.main()
