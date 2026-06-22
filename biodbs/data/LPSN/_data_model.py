"""Data model for LPSN API responses."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LPSNEntry:
    """A single LPSN taxon record."""

    id: Optional[int]
    full_name: Optional[str] = None
    category: Optional[str] = None
    authority: Optional[str] = None
    validly_published: Optional[str] = None
    nomenclatural_status: Optional[str] = None
    lpsn_taxonomic_status: Optional[str] = None
    lpsn_correct_name_id: Optional[int] = None
    lpsn_parent_id: Optional[int] = None
    type_strain_names: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LPSNEntry":
        """Create an entry while preserving unknown fields in ``raw``."""
        value = data.get("id")
        entry_id = int(value) if value is not None else None
        strains = data.get("type_strain_names") or []
        if isinstance(strains, str):
            strains = [strains]
        return cls(
            id=entry_id,
            full_name=data.get("full_name"),
            category=data.get("category"),
            authority=data.get("authority"),
            validly_published=data.get("validly_published"),
            nomenclatural_status=data.get("nomenclatural_status"),
            lpsn_taxonomic_status=data.get("lpsn_taxonomic_status"),
            lpsn_correct_name_id=data.get("lpsn_correct_name_id"),
            lpsn_parent_id=data.get("lpsn_parent_id"),
            type_strain_names=list(strains),
            raw=dict(data),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the original API record."""
        return dict(self.raw)
