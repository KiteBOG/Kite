from typing import Dict, Tuple

WPF_TO_TK: Dict[str, Tuple[str, str]] = {
    "Window": ("tk", "Toplevel"),
    "Grid": ("tk", "Frame"),
    "StackPanel": ("tk", "Frame"),
    "DockPanel": ("tk", "Frame"),
    "Button": ("ttk", "Button"),
    "TextBlock": ("ttk", "Label"),
    "TextBox": ("ttk", "Entry"),
    "ListBox": ("tk", "Listbox"),
    "ComboBox": ("ttk", "Combobox"),
    "CheckBox": ("ttk", "Checkbutton"),
    "RadioButton": ("ttk", "Radiobutton"),
}
