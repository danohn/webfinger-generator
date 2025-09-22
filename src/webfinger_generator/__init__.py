"""Public interface for the WebFinger generator library."""

from importlib import metadata

from .jrd import JRD, JRDValidationError, Link, generate_jrd

try:  # pragma: no cover - fallback for editable installs
    __version__ = metadata.version("webfinger-generator")
except metadata.PackageNotFoundError:  # pragma: no cover - local build metadata
    __version__ = "0.0.0"

__all__ = ["JRD", "Link", "JRDValidationError", "generate_jrd", "__version__"]
