"""Pre-commit hook for trimming spaces in file and directory names."""

from .trim_spaces_in_paths import main

__all__ = ["main"]
