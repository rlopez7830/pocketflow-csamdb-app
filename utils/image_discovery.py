"""Image discovery utility.

Searches valid directories for TIFF files whose filenames case-sensitively
contain both the VID and the keyword HBI.
"""

import logging
import os

logger = logging.getLogger(__name__)

REQUIRED_EXTENSION = ".tiff"
REQUIRED_KEYWORD = "HBI"


def discover_matching_images(vid, existing_directories):
    """Find all matching TIFF image files across valid directories.

    A file is a valid candidate if:
    1. Its filename case-sensitively contains the VID.
    2. Its filename case-sensitively contains 'HBI'.
    3. Its extension is exactly '.tiff'.

    Args:
        vid: The Visual ID string (case-sensitive match).
        existing_directories: A list of validated directory paths.

    Returns:
        A deduplicated list of dicts with keys: file_name, absolute_path,
        source_directory.
    """
    matched = []
    seen_paths = set()

    for directory in existing_directories:
        try:
            entries = os.listdir(directory)
        except OSError:
            logger.warning("Could not list directory: %s", directory)
            continue

        for entry in entries:
            if not entry.endswith(REQUIRED_EXTENSION):
                continue
            if vid not in entry:
                continue
            if REQUIRED_KEYWORD not in entry:
                continue

            full_path = os.path.join(directory, entry)
            if full_path in seen_paths:
                continue

            seen_paths.add(full_path)
            matched.append({
                "file_name": entry,
                "absolute_path": full_path,
                "source_directory": directory,
            })
            logger.info("Matched image: %s", full_path)

    logger.info("Found %d matching image files", len(matched))
    return matched
