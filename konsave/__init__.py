"""Top-level Konsave package."""

from importlib.metadata import distribution, PackageNotFoundError

try:
    __version__ = distribution(__name__).version
except PackageNotFoundError:
    # Package is not installed
    pass
