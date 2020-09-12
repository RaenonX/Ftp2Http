"""Path info object."""
from typing import Generator, Tuple


class PathInfo:
    """
    Object for the convenience on processing path-related operations.

    Returned path will always start from a slash (``/``), and end with a slash (``/``).
    """

    def __init__(self, path: str):
        if not path.startswith("/"):
            path = f"/{path}"
        if not path.endswith("/"):
            path = f"{path}/"

        self._path = path

    @property
    def full_path(self) -> str:
        """Get the full path. This always starts from "/" and end with "/"."""
        return self._path

    @property
    def full_path_for_url(self) -> str:
        """This is same as ``self.full_path`` with the beginning "/" stripped off."""
        return self._path[1:]

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
        for section in self._path.split("/"):
            if not section:
                continue

            ret += f"{section}/"
            yield section, ret
