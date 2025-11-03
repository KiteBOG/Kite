import os
import re
from typing import Dict, List, Any
from ..model import UiNode
from ..utils.fs import find_files, read_text
from ..utils.naming import safe_name

# Control types we'll consider as real UI elements
_ACCEPT_TYPES = {
    'Form','Control','Button','Panel','RichTextBox','Label','TextBox','PictureBox','ComboBox','ListBox','TreeView','ListView',
    'GroupBox','TabControl','TabPage','ProgressBar','TrackBar','NumericUpDown','DateTimePicker','SplitContainer','FlowLayoutPanel',
    'TableLayoutPanel','ToolStrip','StatusStrip','MenuStrip','CheckedListBox','MaskedTextBox','HScrollBar','VScrollBar',
    # custom seen in project
    'CircleButton','RoundedContextMenu'
}

_inst_pat = re.compile(r"(?:this\.)?(?P<name>\w+)\s*=\s*new\s+(?P<type>[\w\.]+)\(\)\s*;", re.MULTILINE)
# var btn = new Button(...){ Prop=..., ... };
_inst_obj_pat = re.compile(r"(?P<name>\w+)\s*=\s*new\s+(?P<type>[\w\.]+)\s*(?:\((?P<args>[^)]*)\))?\s*(\{(?P<init>.*?)\})?\s*;", re.S)
_prop_pat = re.compile(r"(?:this\.)?(?P<name>\w+)\.(?P<prop>\w+)\s*=\s*(?P<value>.+?);\s*$", re.MULTILINE)
_add_form_pat = re.compile(r"this\.Controls\.Add\(\s*(?:this\.)?(?P<child>\w+)\s*\)\s*;", re.MULTILINE)
_add_parent_pat = re.compile(r"(?:this\.)?(?P<parent>\w+)\.Controls\.Add\(\s*(?:this\.)?(?P<child>\w+)\s*\)\s*;", re.MULTILINE)
_addrange_form_pat = re.compile(r"this\.Controls\.AddRange\(\s*new\s+[\w\.]+\[\]\s*\{(?P<list>[^}]*)\}\s*\)\s*;", re.S)
_addrange_parent_pat = re.compile(r"(?:this\.)?(?P<parent>\w+)\.Controls\.AddRange\(\s*new\s+[\w\.]+\[\]\s*\{(?P<list>[^}]*)\}\s*\)\s*;", re.S)
_class_form_pat = re.compile(r"partial\s+class\s+(?P<name>\w+)\s*:\s*Form", re.MULTILINE)
_form_text_pat = re.compile(r"this\.Text\s*=\s*\"(?P<text>.*?)\";")
_form_size_pat = re.compile(r"this\.ClientSize\s*=\s*new\s+(?:System\.Drawing\.)?Size\((?P<w>\d+),\s*(?P<h>\d+)\)\s*;")
_location_pat = re.compile(r"new\s+(?:System\.Drawing\.)?Point\((?P<x>-?\d+),\s*(?P<y>-?\d+)\)")
_size_pat = re.compile(r"new\s+(?:System\.Drawing\.)?Size\((?P<w>\d+),\s*(?P<h>\d+)\)")
_padding_pat = re.compile(r"new\s+(?:System\.Windows\.Forms\.)?Padding\((?P<a>\d+)(?:\s*,\s*(?P<b>\d+)\s*,\s*(?P<c>\d+)\s*,\s*(?P<d>\d+))?\)")
_color_argb_pat = re.compile(r"Color\.FromArgb\((?P<r>\d+)\s*,\s*(?P<g>\d+)\s*,\s*(?P<b>\d+)\)")
_color_name_pat = re.compile(r"(?:System\.Drawing\.)?Color\.(?P<name>\w+)")
_dockstyle_pat = re.compile(r"DockStyle\.(?P<val>\w+)")
_string_pat = re.compile(r'\"(.*?)(?<!\\)\"')


def _split_object_init(s: str):
    parts = []
    buf = ''
    depth = 0
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth = max(0, depth-1)
        if ch == ',' and depth == 0:
            parts.append(buf.strip())
            buf = ''
        else:
            buf += ch
    if buf.strip():
        parts.append(buf.strip())
    kv = []
    for p in parts:
        if '=' in p:
            k, v = p.split('=', 1)
            kv.append((k.strip(), v.strip()))
    return kv


class WinFormsParser:
    def parse_project(self, root: str) -> List[UiNode]:
        files = find_files(root, patterns=["*.Designer.cs"]) or []
        nodes: List[UiNode] = []
        for f in files:
            try:
                node = self.parse_designer(f)
                if node:
                    nodes.append(node)
            except Exception:
                continue
        # If no nodes or nodes lack children, try parsing code-behind .cs
        if not nodes or all(len(n.children) == 0 for n in nodes):
            code_files = [p for p in (find_files(root, patterns=["*.cs"]) or []) if not p.endswith(".Designer.cs")]
            for cf in code_files:
                try:
                    cnode = self.parse_code(cs_path=cf)
                    if cnode:
                        nodes.append(cnode)
                except Exception:
                    continue
        return nodes

    def parse_designer(self, path: str) -> UiNode:
        text = read_text(path)
        # Guess form name from filename
        form_name = os.path.basename(path).replace(".Designer.cs", "")
        root = UiNode(type="Form", name=safe_name(form_name), properties={}, children=[])

        # Collect control types
        controls: Dict[str, Dict[str, Any]] = {}
        for m in _inst_pat.finditer(text):
            name = m.group("name")
            typ = m.group("type").split(".")[-1]
            # Skip designer-only containers
            if name == "components" or typ.endswith("Container") or typ.endswith("IContainer"):
                continue
            controls[name] = {"type": typ, "props": {}, "children": []}

        # Properties
        for m in _prop_pat.finditer(text):
            name = m.group("name")
            prop = m.group("prop")
            val = m.group("value").strip()
            parsed = self._parse_value(prop, val)
            # Treat 'this' and 'base' as the form instance
            if name in ("this", "base"):
                if prop in ("Text", "ClientSize", "Size", "Width", "Height", "BackColor", "ForeColor"):
                    root.properties[prop] = parsed
                continue
            if name == form_name:
                root.properties[prop] = parsed
            else:
                if name not in controls:
                    controls[name] = {"type": "Control", "props": {}, "children": []}
                controls[name]["props"][prop] = parsed

        # Parent-child (form-level adds)
        for m in _add_form_pat.finditer(text):
            child = m.group("child")
            if child not in controls:
                controls[child] = {"type": "Control", "props": {}, "children": []}
            controls[child]["parent"] = form_name
        # AddRange for form
        for m in _addrange_form_pat.finditer(text):
            inner = m.group("list")
            for token in inner.split(','):
                nm = token.strip()
                if not nm:
                    continue
                nm = nm.replace('this.', '').strip()
                if nm not in controls:
                    controls[nm] = {"type": "Control", "props": {}, "children": []}
                controls[nm]["parent"] = form_name
        # Parent-child (panel/groupbox etc.)
        for m in _add_parent_pat.finditer(text):
            parent = m.group("parent")
            child = m.group("child")
            if child not in controls:
                controls[child] = {"type": "Control", "props": {}, "children": []}
            controls[child]["parent"] = parent
        for m in _addrange_parent_pat.finditer(text):
            parent = m.group("parent")
            inner = m.group("list")
            for token in inner.split(','):
                nm = token.strip().replace('this.', '').strip()
                if not nm:
                    continue
                if nm not in controls:
                    controls[nm] = {"type": "Control", "props": {}, "children": []}
                controls[nm]["parent"] = parent

        # Attach to tree
        name_to_node: Dict[str, UiNode] = {}
        for name, data in controls.items():
            node = UiNode(type=data["type"], name=safe_name(name), properties=data["props"], children=[])
            name_to_node[name] = node

        # Determine parents and build hierarchy
        for name, data in controls.items():
            parent = data.get("parent")
            node = name_to_node[name]
            if parent and parent in name_to_node:
                node.parent = name_to_node[parent]
                name_to_node[parent].children.append(node)
            else:
                node.parent = root
                root.children.append(node)

        # Form-level props
        form_text = _form_text_pat.search(text)
        if form_text:
            root.properties["Text"] = form_text.group("text")
        form_size = _form_size_pat.search(text)
        if form_size:
            root.properties["ClientSize"] = {"w": int(form_size.group("w")), "h": int(form_size.group("h"))}

        return root

    def parse_code(self, cs_path: str) -> UiNode | None:
        text = read_text(cs_path)
        m = _class_form_pat.search(text)
        if not m:
            return None
        form_name = m.group("name")
        root = UiNode(type="Form", name=safe_name(form_name), properties={}, children=[])
        controls: Dict[str, Dict[str, Any]] = {}
        # Object initializers and simple news
        for m in _inst_obj_pat.finditer(text):
            name = m.group("name")
            typ = m.group("type").split(".")[-1]
            if name == "components":
                continue
            if typ not in _ACCEPT_TYPES:
                continue
            controls.setdefault(name, {"type": typ, "props": {}, "children": []})
            init = m.group("init")
            if init:
                for p, v in _split_object_init(init):
                    controls[name]["props"][p] = self._parse_value(p, v)
        for m in _inst_pat.finditer(text):
            name = m.group("name")
            typ = m.group("type").split(".")[-1]
            if name == "components":
                continue
            if typ not in _ACCEPT_TYPES:
                continue
            controls.setdefault(name, {"type": typ, "props": {}, "children": []})
        # Properties
        for m in _prop_pat.finditer(text):
            name = m.group("name")
            prop = m.group("prop")
            val = m.group("value").strip()
            if name in ("this", "base"):
                if prop in ("Text", "ClientSize", "Size", "Width", "Height", "BackColor", "ForeColor"):
                    root.properties[prop] = self._parse_value(prop, val)
                continue
            if name not in controls:
                continue
            controls[name]["props"][prop] = self._parse_value(prop, val)
        # Parent-child relationships
        for m in _add_form_pat.finditer(text):
            child = m.group("child")
            if child not in controls:
                continue
            controls[child]["parent"] = form_name
        for m in _addrange_form_pat.finditer(text):
            inner = m.group("list")
            for token in inner.split(','):
                nm = token.strip().replace('this.', '').strip()
                if nm and nm in controls:
                    controls[nm]["parent"] = form_name
        for m in _add_parent_pat.finditer(text):
            parent = m.group("parent")
            child = m.group("child")
            if child not in controls:
                continue
            controls[child]["parent"] = parent
        for m in _addrange_parent_pat.finditer(text):
            parent = m.group("parent")
            inner = m.group("list")
            for token in inner.split(','):
                nm = token.strip().replace('this.', '').strip()
                if nm and nm in controls:
                    controls[nm]["parent"] = parent
        # Build nodes
        name_to_node: Dict[str, UiNode] = {}
        for name, data in controls.items():
            node = UiNode(type=data["type"], name=safe_name(name), properties=data["props"], children=[])
            name_to_node[name] = node
        for name, data in controls.items():
            parent = data.get("parent")
            node = name_to_node[name]
            if parent and parent in name_to_node:
                node.parent = name_to_node[parent]
                name_to_node[parent].children.append(node)
            else:
                node.parent = root
                root.children.append(node)
        return root

    def _parse_value(self, prop: str, val: str) -> Any:
        if _location_pat.search(val):
            m = _location_pat.search(val)
            return {"x": int(m.group("x")), "y": int(m.group("y"))}
        if _size_pat.search(val):
            m = _size_pat.search(val)
            return {"w": int(m.group("w")), "h": int(m.group("h"))}
        if _padding_pat.search(val):
            m = _padding_pat.search(val)
            a = int(m.group('a'))
            b = m.group('b')
            if not b:
                return a
            return (a, int(m.group('b')), int(m.group('c')), int(m.group('d')))
        if _color_argb_pat.search(val):
            m = _color_argb_pat.search(val)
            r, g, b = int(m.group('r')), int(m.group('g')), int(m.group('b'))
            return f"#{r:02X}{g:02X}{b:02X}"
        if _dockstyle_pat.search(val):
            m = _dockstyle_pat.search(val)
            return m.group('val')
        if _color_name_pat.fullmatch(val.strip()):
            m = _color_name_pat.fullmatch(val.strip())
            return m.group('name')
        if val.endswith(")") and "Color" in val:
            # Simplistic fallback
            parts = val.split('.')
            return parts[-1].rstrip(")")
        sm = _string_pat.search(val)
        if sm:
            return sm.group(1)
        if val.isdigit():
            return int(val)
        if val.lower() in ("true", "false"):
            return val.lower() == "true"
        return val
