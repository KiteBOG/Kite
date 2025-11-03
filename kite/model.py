from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class UiNode:
    type: str
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List["UiNode"] = field(default_factory=list)
    parent: Optional["UiNode"] = None
