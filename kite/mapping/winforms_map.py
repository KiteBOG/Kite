from typing import Dict, Tuple

WINFORMS_TO_TK: Dict[str, Tuple[str, str]] = {
    "Form": ("tk", "Tk"),
    "Button": ("ttk", "Button"),
    "Label": ("ttk", "Label"),
    "TextBox": ("ttk", "Entry"),
    "MaskedTextBox": ("ttk", "Entry"),
    "RichTextBox": ("tk", "Text"),
    "ListBox": ("tk", "Listbox"),
    "ListView": ("ttk", "Treeview"),
    "TreeView": ("ttk", "Treeview"),
    "ComboBox": ("ttk", "Combobox"),
    "CheckBox": ("ttk", "Checkbutton"),
    "RadioButton": ("ttk", "Radiobutton"),
    "GroupBox": ("ttk", "Labelframe"),
    "Panel": ("tk", "Frame"),
    "FlowLayoutPanel": ("ttk", "Frame"),
    "TableLayoutPanel": ("ttk", "Frame"),
    "SplitContainer": ("ttk", "Frame"),
    "TabControl": ("ttk", "Notebook"),
    "TabPage": ("ttk", "Frame"),
    "PictureBox": ("tk", "Label"),
    "ProgressBar": ("ttk", "Progressbar"),
    "TrackBar": ("ttk", "Scale"),
    "NumericUpDown": ("widgets", "NumericUpDown"),
    "DateTimePicker": ("widgets", "DatePicker"),
    "MenuStrip": ("widgets", "MenuBar"),
    "StatusStrip": ("widgets", "StatusBar"),
    "ToolStrip": ("widgets", "ToolBar"),
    "DataGridView": ("widgets", "DataGrid"),
    "LinkLabel": ("widgets", "HyperlinkLabel"),
}

# Basic property map WinForms -> Tk kwargs
PROP_MAP: Dict[str, str] = {
    "Text": "text",
    "Enabled": "state",
    "Visible": "visible",
    "BackColor": "background",
    "ForeColor": "foreground",
}
