"""Data models and containers for biological database APIs."""

# Base classes are available for subclassing
from biodbs.data._base import BaseFetchedData, BaseDBManager

__all__ = [
    "BaseFetchedData",
    "BaseDBManager",
]
