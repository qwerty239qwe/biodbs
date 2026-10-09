"""Parse an NCBI taxdump into an in-memory hub table.

Accepts a directory of ``.dmp`` files or a ``*.tar.gz`` (e.g. ``new_taxdump.tar.gz``
from ``biodbs.fetch.ncbi_download_taxdump``). Pure standard library.
"""

from __future__ import annotations

import io
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


def _split_dmp(line: str) -> list[str]:
    # Rows look like: "562\t|\tEscherichia coli\t|\t\t|\tscientific name\t|"
    return [cell.strip() for cell in line.rstrip("\n").rstrip("|").split("\t|\t")]


@dataclass
class NCBITaxonomy:
    names: dict[int, str] = field(default_factory=dict)          # taxid -> scientific name
    ranks: dict[int, str] = field(default_factory=dict)          # taxid -> rank
    parents: dict[int, int] = field(default_factory=dict)        # taxid -> parent taxid
    merged: dict[int, int] = field(default_factory=dict)         # old taxid -> new taxid
    name_to_taxid: dict[str, int] = field(default_factory=dict)  # lowercased name -> taxid

    def resolve(self, taxid: int) -> int:
        return self.merged.get(taxid, taxid)

    def name(self, taxid: int) -> str | None:
        return self.names.get(self.resolve(taxid))

    def rank(self, taxid: int) -> str | None:
        return self.ranks.get(self.resolve(taxid))

    def parent(self, taxid: int) -> int | None:
        return self.parents.get(self.resolve(taxid))

    def taxid_for_name(self, name: str) -> int | None:
        return self.name_to_taxid.get(name.strip().lower())

    def lineage(self, taxid: int) -> list[tuple[str, str]]:
        chain: list[tuple[str, str]] = []
        current = self.resolve(taxid)
        seen: set[int] = set()
        while current and current not in seen:
            seen.add(current)
            chain.append((self.ranks.get(current, "no rank"), self.names.get(current, str(current))))
            parent = self.parents.get(current)
            if parent is None or parent == current:  # root is its own parent
                break
            current = parent
        return list(reversed(chain))


def _feed_nodes(tax: NCBITaxonomy, lines: Iterable[str]) -> None:
    for line in lines:
        cells = _split_dmp(line)
        if len(cells) < 3:
            continue
        taxid, parent, rank = int(cells[0]), int(cells[1]), cells[2]
        tax.parents[taxid] = parent
        tax.ranks[taxid] = rank


def _feed_names(tax: NCBITaxonomy, lines: Iterable[str]) -> None:
    for line in lines:
        cells = _split_dmp(line)
        if len(cells) < 4:
            continue
        taxid, name_txt, name_class = int(cells[0]), cells[1], cells[3]
        if name_class == "scientific name":
            tax.names[taxid] = name_txt
        # index every name class (scientific + synonyms + equivalents) for lookup
        tax.name_to_taxid.setdefault(name_txt.lower(), taxid)


def _feed_merged(tax: NCBITaxonomy, lines: Iterable[str]) -> None:
    for line in lines:
        cells = _split_dmp(line)
        if len(cells) < 2:
            continue
        tax.merged[int(cells[0])] = int(cells[1])


def load_taxdump(source: str | Path) -> NCBITaxonomy:
    tax = NCBITaxonomy()
    path = Path(source)
    readers = {"nodes.dmp": _feed_nodes, "names.dmp": _feed_names, "merged.dmp": _feed_merged}
    if path.is_dir():
        for filename, feed in readers.items():
            file_path = path / filename
            if file_path.exists():
                with file_path.open(encoding="utf-8") as handle:
                    feed(tax, handle)
    else:
        with tarfile.open(path, "r:*") as archive:
            for filename, feed in readers.items():
                member = next((m for m in archive.getmembers() if Path(m.name).name == filename), None)
                if member is None:
                    continue
                extracted = archive.extractfile(member)
                if extracted is not None:
                    feed(tax, io.TextIOWrapper(extracted, encoding="utf-8"))
    return tax
