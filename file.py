"""Module for all file controls including file info parsing."""
import stat
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto
from math import log
from pathlib import Path
from typing import List, Dict, Generator, Optional, BinaryIO

from path import PathInfo

__all__ = ("get_file_entries", "retrieve_file")


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
    def parse_from_mode(mode: int) -> "EntryType":
        """Parse the entry type using ``mode`` in ``os.stat_result().st_mode``."""
        return EntryType.DIRECTORY if stat.S_ISDIR(mode) else EntryType.FILE

    def __str__(self):
        if self == EntryType.DIRECTORY:
            return "D"
        elif self == EntryType.FILE:
            return "F"

        return repr(self)


@dataclass
class FileEntry:
    entry_type: EntryType
    file_name: str
    file_size: FileSize
    modified_utc_str: str

    @staticmethod
    def parse_from_path(pure_path: Path) -> "FileEntry":
        """Parse ``entry`` yielded from ``Path("Y:/").iterdir()``."""
        file_stats = pure_path.stat()

        entry_type = EntryType.parse_from_mode(file_stats.st_mode)
        file_size = FileSize(file_stats.st_size)
        modified_utc = datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        return FileEntry(entry_type, pure_path.name, file_size, modified_utc)

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


def get_file_entries(path: str = "") -> Generator[FileEntry, None, None]:
    """
    Get a :class:`generator` which yields files and directories under the current working directory.

    :raises FileNotFoundError: path not found
    :raises NotADirectoryError: path is not a directory
    """
    path = Path(PathInfo(path).full_path_with_root)

    if not path.exists():
        raise FileNotFoundError(path)

    if not path.is_dir():
        raise NotADirectoryError(path)

    for path_in_dir in path.iterdir():
        yield FileEntry.parse_from_path(path_in_dir)


class FileForDownload:
    def __init__(self, path_info: PathInfo):
        """
        Initialize a :class:`FileStream`.

        :param path_info: a `PathInfo` object of the file
        :raises FileNotFoundError: file at `path_info` not found
        :raises PathIsDirectoryError: `path_info` is a directory
        """
        self._path = Path(path_info.full_path_with_root)

        if not self._path.exists():
            raise FileNotFoundError()

        if self._path.is_dir():
            raise IsADirectoryError()

        self._file_name = self._path.name
        self._file_size = self._path.stat().st_size

    @property
    def file_name(self) -> str:
        """Get the file name."""
        return self._file_name

    @property
    def file_size(self) -> int:
        """Get the file size in bytes."""
        return self._file_size

    @property
    def stream(self) -> BinaryIO:
        return open(self._path.resolve(strict=True), "rb")


def retrieve_file(path_info: PathInfo) -> Optional[FileForDownload]:
    """
    Retrieve the file stream for file downloading.

    :raises FileNotFoundError: path not found
    :raises IsADirectoryError: path is a directory
    """
    return FileForDownload(path_info)
