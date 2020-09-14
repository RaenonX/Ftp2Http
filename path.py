"""Path info object."""
from typing import Generator, Tuple

__all__ = ("PathInfo",)


class PathInfo:
    """
    Object for the convenience on processing path-related operations.

    Returned path will always start from a slash (``/``), and end with a slash (``/``).
    """
    ROOT = "Y:"

    def __init__(self, path_without_root: str):
        if not path_without_root.startswith("/"):
            path_without_root = f"/{path_without_root}"
        if not path_without_root.endswith("/"):
            path_without_root = f"{path_without_root}/"

        self._path = f"{PathInfo.ROOT}{path_without_root}"

    @property
    def full_path_with_root(self) -> str:
        """Get the full path with the configured root. This always starts from ``ROOT`` and ends with "/"."""
        return self._path

    @property
    def full_path(self) -> str:
        """Get the full path without root. This always starts from "/" and end with "/"."""
        return self._path[len(self.ROOT):]

    @property
    def full_path_for_url(self) -> str:
        """This is same as ``self.full_path`` with the beginning "/" stripped off."""
        return self.full_path[1:]

    @property
    def full_paths_from_root(self) -> Generator[Tuple[str, str], None, None]:
        """
        Get the full paths and the corresponding section from the root to current.

        Returned paths will always starts from "/" and end with "/".

        Examples
        ========
        If there's a path like this ``/A/B/C/``, the following paths will be returned in the order below:

        - ``/``

        - ``/A/``

        - ``/A/B/``

        - ``/A/B/C/``
        """
        ret = ""
        for section in self.full_path.split("/"):
            if not section:
                continue

            ret += f"{section}/"
            yield section, ret
