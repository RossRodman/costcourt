"""CostCourt: AI-powered review of construction estimates.

Three agents (estimator, engineer, contractor's advocate) debate a
construction estimate; a judge weighs their arguments and issues a verdict.
The whole deliberation is preserved in a report.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("costcourt")
except PackageNotFoundError:  # running from a source tree without install
    __version__ = "0.0.0+local"

__all__ = ["__version__"]
