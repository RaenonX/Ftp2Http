"""Module for all FTP controls including file info parsing."""
import ftplib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto
from io import BytesIO
from math import log
from typing import List, Dict, Generator, Optional

__all__ = ("get_file_entries", "retrieve_file")

ftp = ftplib.FTP("192.168.50.6", user="anonymous")
ftp.encoding = "UTF-8"  # Default is ASCII


class FileSize:
    """File size object for the convenience of rendering it to string."""

    _cache: Dict[int, str] = defaultdict()
    _conv_unit: List[str] = ["B", "KB", "MB", "GB", "TB"]

    def __init__(self, size_byte: int):
        self._size = size_byte

    def _format_size(self):
        unit_base = min(int(log(self._size, 1024)), len(self._conv_unit))
        unit = self._conv_unit[unit_base]
        div_base = 1024 ** unit_base

        return f"{self._size / div_base:,.1f} {unit}"

    @property
    def formatted(self) -> str:
        """
        Get the size in formatted string.

        The divisor used is 1024, which means that the returned unit is KB (or so), **NOT** KiB.

        String format
        =============

        The returned string will have 1 floating point with comma separating the numbers.
        If the number after formatting is > 1000, the comma separation will be applied.

        The size will be automatically being formatted to either one of these:

        - B

        - KB

        - MB

        - GB

        - TB

        If the size goes beyond 1024 TB or below 1 KB, no further formatting will be applied.

        Examples
        ========
        ``23095254`` → ``22.0 MB``
        ``1002`` → ``1,002 B``
        ``10000046545656476620`` → ``8,881.8 TB``
        """
        if self._size not in self._cache:
            self._cache[self._size] = self._format_size()

        return self._cache[self._size]

    @property
    def original(self) -> str:
        """Get the original size in terms of B with comma separation if applicable."""
        return f"{self._size:,} B"

    def __repr__(self):
        return self.formatted


class EntryType(Enum):
    DIRECTORY = auto()
    FILE = auto()

    @staticmethod
    def parse_from_mlsd(name: str) -> "EntryType":
        """Parse the entry type using ``name`` returned from ``ftp.mlsd()``"""
        if name.lower() == "dir":
            return EntryType.DIRECTORY
        elif name.lower() == "file":
            return EntryType.FILE

        raise ValueError(f"Unrecognized file type name: {name}")

    def __str__(self):
        if self == EntryType.DIRECTORY:
            return "D"
        elif self == EntryType.FILE:
            return "F"

        return repr(self)


@dataclass
class FTPFile:
    entry_type: EntryType
    file_name: str
    file_size: FileSize
    modified_utc_str: str

    @staticmethod
    def parse_from_mlsd(entry) -> "FTPFile":
        """Parse ``entry`` returned from ``ftp.mlsd()``."""
        file_name, info = entry
        entry_type = EntryType.parse_from_mlsd(info["type"])
        file_size = FileSize(int(info["size"]))
        modified_utc = (
            datetime
                .strptime(info["modify"], "%Y%m%d%H%M%S")
                .replace(tzinfo=timezone.utc)
                .strftime("%Y-%m-%d %H:%M:%S")
        )

        return FTPFile(entry_type, file_name, file_size, modified_utc)

    @property
    def is_file(self) -> bool:
        return self.entry_type == EntryType.FILE

    @property
    def is_directory(self) -> bool:
        return self.entry_type == EntryType.DIRECTORY

    def __repr__(self):
        if self.entry_type == EntryType.FILE:
            return f"{self.entry_type} - {self.file_name} ({self.file_size})"
        elif self.entry_type == EntryType.DIRECTORY:
            return f"{self.entry_type} - {self.file_name}"

        raise ValueError(f"Unhandled entry type: {self.entry_type}")


def get_file_entries(path: str = "") -> Generator[FTPFile, None, None]:
    """Get a generator which yields files and directories under the current working directory."""
    for entry in ftp.mlsd(path):
        yield FTPFile.parse_from_mlsd(entry)


def retrieve_file(path: str) -> Optional[BytesIO]:
    """Retrieve the file stream for file downloading."""
    file = BytesIO()

    try:
        ftp.retrbinary(f"RETR {path}", file.write)
    except ftplib.error_perm:
        return None

    return BytesIO(file.getvalue())
