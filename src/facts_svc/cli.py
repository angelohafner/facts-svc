"""Command-line entry point for standalone and batch SVG/PNG generation."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from .model import SVCConfig, presets
from .renderer import render_svg


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="facts-svc", description="Render modular, editable SVC schematics"
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--preset", choices=tuple(presets()), default=None)
    source.add_argument("--config", type=Path, help="JSON file with custom SVC topology")
    source.add_argument("--all", action="store_true", help="Render all presets")
    parser.add_argument("--list-presets", action="store_true",
                        help="Print the available built-in presets")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--format", choices=("svg", "png", "both"), default="svg")
    parser.add_argument("--no-transformer", action="store_true",
                        help="Show a direct PCC-to-SVC connection")
    return parser


def _write_png(svg_path: Path) -> Path:
    try:
        import cairosvg
    except ImportError as exc:
        raise SystemExit("PNG output requires: pip install 'facts-svc[png]'") from exc
    png_path = svg_path.with_suffix(".png")
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1600)
    return png_path


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    available = presets()
    if args.list_presets:
        for name in available:
            print(name)
        return 0
    if args.config is not None:
        jobs = [(args.config.stem, SVCConfig.from_json(args.config))]
    elif args.all:
        jobs = list(available.items())
    else:
        name = args.preset or "hybrid"
        jobs = [(name, available[name])]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, config in jobs:
        if args.no_transformer:
            config = replace(config, transformer=False)
        target = args.output_dir / f"{name}.svg"
        svg_file = render_svg(config, target)
        paths = [svg_file]
        if args.format in {"png", "both"}:
            paths.append(_write_png(svg_file))
            if args.format == "png":
                svg_file.unlink()
                paths.pop(0)
        manifest.append({"preset": name, "config": config.to_dict(),
                         "files": [p.name for p in paths]})
        for path in paths:
            print(path)
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    print(manifest_path)
    return 0
