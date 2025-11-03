import argparse
from .converter import Converter
from .utils.log import log


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kite", description="Convert .NET UIs (WinForms/WPF) to Tkinter")
    sub = p.add_subparsers(dest="cmd", required=True)

    conv = sub.add_parser("convert", help="Convert a .NET project to Tkinter")
    conv.add_argument("--input", "-i", required=True, help="Path to .NET project root (.sln/.csproj) or source dir")
    conv.add_argument("--output", "-o", required=True, help="Output directory for generated Tkinter project")
    conv.add_argument("--main-window", default=None, help="Optional main window/form name to start")
    conv.add_argument("--overwrite", action="store_true", help="Overwrite output directory if exists")

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "convert":
        log.info("Starting conversion", input=args.input, output=args.output)
        Converter().convert(input_path=args.input, output_dir=args.output, main_window=args.main_window, overwrite=args.overwrite)
        log.info("Done", output=args.output)
