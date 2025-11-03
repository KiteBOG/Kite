from typing import Optional

NAMED_COLORS = {
    'Black': '#000000', 'White': '#FFFFFF', 'Red': '#FF0000', 'Green': '#00FF00', 'Blue': '#0000FF',
    'Yellow': '#FFFF00', 'Gray': '#808080', 'LightGray': '#D3D3D3', 'DarkGray': '#A9A9A9',
    'Transparent': '#FFFFFF', 'Window': '#FFFFFF',
}

def color_to_hex(name_or_hex: Optional[str]) -> str:
    if not name_or_hex:
        return '#000000'
    s = str(name_or_hex).strip()
    if s.startswith('#') and (len(s) in (4, 7)):
        return s
    return NAMED_COLORS.get(s, '#000000')
