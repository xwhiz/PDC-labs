from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class User:
    id: Optional[str]
    name: Optional[str]
    address: Any
