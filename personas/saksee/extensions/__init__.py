"""Install, list, validate, update, and remove SakThai extensions (skill/MCP bundles from git)."""

from __future__ import annotations

from .install import (
    ExtensionError,
    ExtensionInfo,
    ExtensionUpdateResult,
    ExtensionValidationResult,
    InstallResult,
    extensions_dir,
    get_extension_info,
    install_extension,
    list_extensions,
    remove,
    update_extension,
    validate_extension,
    validate_extension_manifest,
)

__all__ = [
    "ExtensionError",
    "ExtensionInfo",
    "ExtensionUpdateResult",
    "ExtensionValidationResult",
    "InstallResult",
    "extensions_dir",
    "get_extension_info",
    "install_extension",
    "list_extensions",
    "remove",
    "update_extension",
    "validate_extension",
    "validate_extension_manifest",
]
