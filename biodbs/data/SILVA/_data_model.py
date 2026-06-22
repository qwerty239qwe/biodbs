"""Data model for SILVA release file listings."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SILVAFile:
    """A file or directory in a SILVA release listing."""

    name: str
    url: str
    size: Optional[str] = None
    modified: Optional[str] = None
    is_dir: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "size": self.size,
            "modified": self.modified,
            "is_dir": self.is_dir,
        }


@dataclass
class SILVARelease:
    """A SILVA archive release."""

    name: str
    url: str
    modified: Optional[str] = None

    def to_dict(self) -> dict:
        return {"name": self.name, "url": self.url, "modified": self.modified}

