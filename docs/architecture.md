# Modular architecture for future FACTS diagrams

`facts_svc` is a **diagram generator**, not a circuit solver. It intentionally separates electrical descriptions, reusable vector symbols, and topology-dependent layout.

| Module | Role | Reusability |
| --- | --- | --- |
| `model.py` | Frozen SVC and branch topology configurations, validation, preset factories | Can be replaced by a future shared FACTS domain model |
| `svg.py` | SVG primitives, style, group/layer infrastructure, editable scientific labels | Generic; suitable for all FACTS and HVDC drawings |
| `symbols.py` | SCR, antiparallel valve, inductor, capacitor, transformer, ground | Generic electrical schematic symbols |
| `renderer.py` | Positioning, buses, wires, labels, branch composition | SVC-specific composition |
| `cli.py` | JSON input, gallery generation, optional PNG export | Easily generalized to other diagram families |

## Planned multi-project consolidation

1. Keep new developments in this repository. Do not add imports that depend on a sibling git clone or a user-specific file path.
2. Later extract `svg.py` and `symbols.py` into a separate installable package (for example `power-diagrams-core`) once other equipment types require them.
3. Implement new device renderers (TCSC, STATCOM, UPFC, HVDC/LCC) on the shared SVG primitives, each with its own independent topology model.
4. Preserve vector-editable labels, mathematically correct symbol orientations, and automated topology checks.
5. Consider a pluggable renderer protocol if direct Schemdraw backends or interactive HTML become necessary. The current dependency-free backend uses Schemdraw SCR path primitives when available.

## Electrical scope and limitations

- Each branch is electrically connected between a common secondary bus and a common symbolic shunt return. For **single-line/per-phase illustration**, this makes the branches parallel without claiming the exact phase-neutral or phase-phase wiring of real three-phase banks.
- A TCR is a series reactor and a bidirectional antiparallel SCR valve. With the conventional phase-voltage zero-crossing reference, typical fundamental-frequency firing angles are 90–180 degrees.
- A TSR uses the same reactor/valve geometry but step ON/OFF control.
- A TSC has a small series damping/current-limiting reactor, a capacitor, and an antiparallel SCR valve. It is switched in steps; alpha is not continuously modulated like the TCR.
- An FC is a fixed shunt capacitor; `FILTER` represents a **series** LC branch used as a tuned shunt filter, not two parallel elements.
- A real SVC may include multiple filters, TSC banks, auxiliary switching devices, bus protections, and non-ideal transformer winding connections. The diagram does not determine their ratings, resonance, gate timing, voltages, or dynamic operating point.

## Typography

The SVG graphics use italic scalar variables, including Greek symbols; roman physical units and descriptive subscripts; and reserved bold upright text for matrix symbols. Math labels remain real SVG `<text>/<tspan>` objects editable in Inkscape.

## Origin of vector primitives

The general-purpose SVG grouping and typography patterns, and the SCR geometry/fallback approach, were adapted from the same author's [`three-phase-scr-rectifier-visualizer`](https://github.com/angelohafner/three-phase-scr-rectifier-visualizer) project, especially `rectifier_art.py`. This repository is self-contained; there are no runtime imports from the original project.
