"""Module for all FTP controls including file info parsing."""
import ftplib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto
from math import log
from typing import List, Dict, Generator, Optional

from path import PathInfo

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
        modified_utc = datetime.strptime(info["modify"], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        modified_utc = modified_utc.strftime("%Y-%m-%d %H:%M:%S")

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


class FTPFileStream:
    def __init__(self, ftp_client: ftplib.FTP, path_info: PathInfo, default_block_size: int = 8196):
        """
        Initialize a :class:`FTPFileStream`.

        :param ftp_client: ftp client to establish the connection
        :param path_info: a `PathInfo` object of the file
        :param default_block_size: default block size to be used when calling this object via ``next()`` or ``iter()``
        """
        self._ftp_client: ftplib.FTP = ftp_client
        self._ftp_path: str = path_info.full_path
        try:
            self._file_size: int = ftp_client.size(self._ftp_path)
        except ftplib.error_perm as ex:
            raise FileNotFoundError(self._ftp_path) from ex
        self._file_name: str = self._ftp_path.split(self._ftp_path)[-1]

        self._block_size = default_block_size
        self._conn = None

    @property
    def file_name(self) -> str:
        """Get the file name."""
        return self._file_name

    @property
    def file_size(self) -> int:
        """Get the file size in bytes."""
        return self._file_size

    def read(self, block_size: Optional[int] = None) -> Optional[bytes]:
        """
        Read a binary chunk of data from the connection. If the connection was not established yet, establish it.

        Uses the default block size given during instantiation if ``block_size`` is not specified.

        Returns ``None`` if no further data can be read (reaches EOF).
        """
        if not block_size:
            block_size = self._block_size

        # Check if the connection is established
        if not self._conn:
            # Cannot use ``self.retrbinary()`` because it calls the callback method immediately
            # to store the data in the memory, which is an undesired behavior because large file download will
            # takes all RAM
            #
            # Implementation inspired by the original code of ``self.retrbinary()``
            self._conn = self._ftp_client.transfercmd(f"RETR {self._ftp_path}")

        # Get a chunk of data
        if data := self._conn.recv(block_size):
            return data

        self._conn.close()
        return None

    def __iter__(self, *args, **kwargs):
        for data in self:
            yield data

    def __next__(self, *args, **kwargs):
        if data := self.read(self._block_size):
            return data

        # No data received (reached the end), close the connection
        self._conn.close()
        raise StopIteration()


def retrieve_file(path_info: PathInfo) -> Optional[FTPFileStream]:
    """Retrieve the file stream for file downloading."""
    try:
        return FTPFileStream(ftp, path_info)
    except FileNotFoundError:
        return None
