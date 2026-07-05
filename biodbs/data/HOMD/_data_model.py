"""Data models for HOMD listings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HOMDFile:
    """File or directory exposed by HOMD."""

    name: str
    url: str
    is_dir: bool = False
    category: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "is_dir": self.is_dir,
            "category": self.category,
        }
