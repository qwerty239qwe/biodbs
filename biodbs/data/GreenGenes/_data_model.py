"""Data model for GreenGenes release directory listings."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GreenGenesFile:
    """A file or directory in a GreenGenes release listing."""

    name: str
    url: str
    is_dir: bool = False

    def to_dict(self) -> dict:
        return {"name": self.name, "url": self.url, "is_dir": self.is_dir}


@dataclass
class GreenGenesRelease:
    """A top-level GreenGenes release directory."""

    name: str
    url: str
    modified: Optional[str] = None

    def to_dict(self) -> dict:
        return {"name": self.name, "url": self.url, "modified": self.modified}
