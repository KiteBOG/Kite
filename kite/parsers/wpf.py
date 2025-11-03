import os
import xml.etree.ElementTree as ET
from typing import List
from ..model import UiNode
from ..utils.fs import find_files, read_text
from ..utils.naming import safe_name


class WpfParser:
    def parse_project(self, root: str) -> List[UiNode]:
        files = find_files(root, patterns=["*.xaml"]) or []
        nodes: List[UiNode] = []
        for f in files:
            # Skip resources/app xaml
            base = os.path.basename(f).lower()
            if base.startswith("app."):
                continue
            try:
                nodes.append(self.parse_xaml(f))
            except Exception:
                continue
        return nodes

    def parse_xaml(self, path: str) -> UiNode:
        text = read_text(path)
        root_el = ET.fromstring(text)
        root_type = self._strip_ns(root_el.tag)
        name = safe_name(os.path.splitext(os.path.basename(path))[0])
        root = UiNode(type=root_type, name=name, properties=self._attrs(root_el), children=[])
        self._walk_children(root_el, root)
        return root

    def _walk_children(self, el: ET.Element, node: UiNode) -> None:
        for child in list(el):
            if isinstance(child.tag, str):
                ctype = self._strip_ns(child.tag)
                cnode = UiNode(type=ctype, name=safe_name(child.attrib.get("x:Name") or child.attrib.get("Name") or ctype), properties=self._attrs(child), children=[])
                cnode.parent = node
                node.children.append(cnode)
                self._walk_children(child, cnode)

    def _attrs(self, el: ET.Element):
        props = {}
        for k, v in el.attrib.items():
            if k.endswith("Name") or k.endswith(":Name"):
                continue
            props[self._strip_ns(k)] = v
        return props

    def _strip_ns(self, tag: str) -> str:
        if '}' in tag:
            return tag.split('}', 1)[1]
        return tag
