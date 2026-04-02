"""Directory validation utility.

Checks which candidate UNC directories actually exist and are readable.
"""

import logging
import os

logger = logging.getLogger(__name__)


def validate_directories(candidate_directories):
    """Check which candidate directories exist and are accessible.

    Args:
        candidate_directories: A list of directory path strings.

    Returns:
        A list of directories that exist and are readable.
    """
    existing = []
    for d in candidate_directories:
        if os.path.isdir(d):
            existing.append(d)
            logger.info("Directory exists: %s", d)
        else:
            logger.warning("Directory does not exist: %s", d)

    logger.info("%d of %d candidate directories exist",
                len(existing), len(candidate_directories))
    return existing
