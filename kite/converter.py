from typing import List, Optional
import os

from .parsers.winforms import WinFormsParser
from .parsers.wpf import WpfParser
from .generator.tk_generator import TkGenerator
from .utils.fs import ensure_empty_dir, ensure_dir, write_text, read_text, find_files
from .utils.log import log
from .model import UiNode


class Converter:
    def __init__(self) -> None:
        self.winforms = WinFormsParser()
        self.wpf = WpfParser()
        self.generator = TkGenerator()

    def _detect_kind(self, input_path: str) -> str:
        csproj = find_files(input_path, patterns=["*.csproj"]) or []
        xamls = find_files(input_path, patterns=["*.xaml"]) or []
        designers = find_files(input_path, patterns=["*.Designer.cs"]) or []
        if xamls:
            return "wpf"
        if designers:
            return "winforms"
        # Fallback by inspect .csproj
        if csproj:
            text = read_text(csproj[0])
            if "<UseWPF>true</UseWPF>" in text or "<OutputType>WinExe</OutputType>" in text and ".xaml" in text:
                return "wpf"
        return "winforms"

    def _collect(self, input_path: str, kind: str) -> List[UiNode]:
        if kind == "wpf":
            return self.wpf.parse_project(input_path)
        else:
            return self.winforms.parse_project(input_path)

    def convert(self, input_path: str, output_dir: str, main_window: Optional[str] = None, overwrite: bool = False) -> None:
        input_path = os.path.abspath(input_path)
        # Accept a file path (e.g., .sln/.csproj) by converting to its directory
        input_root = input_path if os.path.isdir(input_path) else os.path.dirname(input_path)
        output_dir = os.path.abspath(output_dir)

        if overwrite:
            ensure_empty_dir(output_dir)
        else:
            ensure_dir(output_dir)

        kind = self._detect_kind(input_root)
        log.info("Detected project kind", kind=kind)
        ui_roots = self._collect(input_root, kind)
        if not ui_roots:
            raise RuntimeError("No windows/forms found to convert.")

        app_pkg_dir = os.path.join(output_dir, "app")
        ensure_dir(app_pkg_dir)
        write_text(os.path.join(app_pkg_dir, "__init__.py"), "")

        generated = []
        for node in ui_roots:
            fname, positions, colors = self.generator.generate_window(app_pkg_dir, node)
            generated.append((node.name, fname, positions, colors))

        self.generator.generate_app(output_dir, generated, main_window, kind)
