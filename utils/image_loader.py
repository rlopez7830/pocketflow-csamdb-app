"""TIFF loader utility.

Reads a TIFF file from disk or network share and returns the raw bytes.
"""

import logging

logger = logging.getLogger(__name__)


def load_tiff(file_path):
    """Load a TIFF file and return its raw bytes.

    Args:
        file_path: The absolute path to the TIFF file.

    Returns:
        The raw file bytes.
    """
    logger.info("Loading TIFF file: %s", file_path)
    with open(file_path, "rb") as f:
        data = f.read()
    logger.info("Loaded %d bytes from %s", len(data), file_path)
    return data
