"""Install, list, and remove SakThai extensions (skill/MCP bundles from git)."""

from __future__ import annotations

from .install import (
                      ExtensionError,
                      ExtensionInfo,
                      InstallResult,
                      extensions_dir,
                      install_extension,
                      list_extensions,
                      remove,
)

__all__ = [
    "ExtensionError",
    "ExtensionInfo",
    "InstallResult",
    "extensions_dir",
    "install_extension",
    "list_extensions",
    "remove",
]
