# Development prompt — modular SVC drawings in Python

Develop and maintain a professional, reusable Python package for generating vector-editable electrical diagrams of **Static VAR Compensators (SVCs)** in the repository `https://github.com/angelohafner/facts-svc`.

Use `https://github.com/angelohafner/three-phase-scr-rectifier-visualizer` as an architectural and graphical reference: reuse or adapt its SVG drawing practices and genuine Schemdraw SCR geometry when helpful, but **do not create a runtime dependency on the other repository**. The long-term objective is to consolidate common symbols and rendering methods into a shared library for SVC, LCC-HVDC, TCSC, STATCOM and other FACTS devices.

**Mandatory requirements**

1. Build a modular Python package using classes, dataclasses, explicit types, small reusable functions and clear separation between topology models, electrical symbol geometry, SVG rendering and CLI/configuration.
2. Draw several functional topologies: TCR-only, FC–TCR, TSC–TCR, TSC–TCR with harmonic filters, multi-bank TSC–TCR and optionally TSR–FC. Permit custom combinations via a validated JSON configuration.
3. Represent **individual SCRs oriented in antiparallel**, not generic switch blocks. TCR = series reactor + antiparallel SCR valve; TSC = current-limiting reactor + capacitor + antiparallel SCR valve; tuned harmonic filter = series L–C shunt branch. The two SCRs must share endpoints without accidental bypasses or open wires.
4. Show PCC, optional coupling transformer, SVC bus, independent shunt branches and a symbolic return. Explicitly label the first diagrams as single-line/per-phase equivalents; do not imply that three-phase delta/wye wiring is specified. Distinguish a TCR's continuous firing-angle operation from TSC/TSR stepped switching.
5. Produce high-resolution, fully editable SVGs suitable for Inkscape; optionally export PNG. Use italic variables (including Greek), upright units and descriptive subscripts, and bold upright matrix names.
6. Use an installable `src/` package, Python 3.10+ compatibility, command-line presets, JSON examples, documentation and automated tests. Keep all Python comments and docstrings in English.
7. Include structural/visual validation: check SVG parsability, element count, opposite SCR orientations, branch-to-bus connections, no valve short circuits, readable labels and no accidental wire discontinuities. Do not confuse a conceptual diagram with an electrical simulation.
8. Preserve a self-contained architecture so future equipment projects can import common drawing primitives without copying entire scripts. Use GitHub commits and continuous integration to retain reproducible results.

**Deliverables:** maintainable Python code; README with install/usage examples; at least four demonstration SVGs; configuration examples; a test suite; and a concise report of electrical/visual checks and known limitations.
