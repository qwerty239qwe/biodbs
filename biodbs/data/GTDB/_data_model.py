"""Data models for GTDB listings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GTDBFile:
    """File or directory exposed by GTDB."""

    name: str
    url: str
    is_dir: bool = False
    size: str = ""
    modified: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "is_dir": self.is_dir,
            "size": self.size,
            "modified": self.modified,
        }
