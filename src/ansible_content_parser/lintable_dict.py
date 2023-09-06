"""Defines LintableDict class."""
import typing

from ansiblelint.file_utils import Lintable


class LintableDict(dict[str, typing.Any]):
    """The LintableDict class."""

    def __init__(self, lintable: Lintable) -> None:
        """Initialize LintableDict."""
        self["base_kind"] = str(lintable.base_kind)
        self["dir"] = str(lintable.dir)
        self["exc"] = None if lintable.exc is None else str(lintable.exc)
        self["filename"] = str(lintable.filename)
        self["kind"] = str(lintable.kind)
        self["name"] = str(lintable.name)
        self["parent"] = None if lintable.parent is None else str(lintable.parent.name)
        self["role"] = str(lintable.role)
        self["stop_processing"] = bool(lintable.stop_processing)
        self["updated"] = bool(lintable.updated)
