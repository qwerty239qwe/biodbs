"""Data model for PR2 GitHub release listings."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PR2Asset:
    """A downloadable file attached to a PR2 release."""

    name: str
    url: str
    size: Optional[int] = None

    def to_dict(self) -> dict:
        return {"name": self.name, "url": self.url, "size": self.size}


@dataclass
class PR2Release:
    """A PR2 GitHub release."""

    tag: str
    url: str
    published: Optional[str] = None
    assets: List[PR2Asset] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "url": self.url,
            "published": self.published,
            "assets": [asset.name for asset in self.assets],
        }
