"""Image path builder utility.

Constructs and validates UNC image paths from ARIES A_OBJ_* query results.
"""

import logging
import os

logger = logging.getLogger(__name__)


def build_image_paths(image_path_results):
    """Construct UNC paths from ARIES image path query results and validate existence.

    For each result row, builds the path as:
        \\\\<image_filer_address>\\<image_relative_path><parameter_value>

    Args:
        image_path_results: A list of dicts from the A_OBJ_* query, each
            containing image_filer_address, image_relative_path, and
            parameter_value keys.

    Returns:
        A list of dicts with keys: file_name, absolute_path,
        source_directory.
    """
    images = []
    seen_paths = set()

    for row in image_path_results:
        server = str(row.get("image_filer_address", "")).strip()
        rel_path = str(row.get("image_relative_path", "")).strip()
        filename = str(row.get("parameter_value", "")).strip()

        if not server or not filename:
            continue

        # Construct UNC path: \\server\relative_path + filename
        base = f"\\\\{server}\\{rel_path}"
        if rel_path and not rel_path.endswith("\\"):
            base += "\\"
        path = base + filename

        if path in seen_paths:
            continue
        seen_paths.add(path)

        if not os.path.isfile(path):
            logger.warning("Image path does not exist: %s", path)
            continue

        images.append({
            "file_name": filename,
            "absolute_path": path,
            "source_directory": os.path.dirname(path),
        })
        logger.info("Valid image path: %s", path)

    logger.info(
        "Found %d valid image files from %d query rows",
        len(images), len(image_path_results),
    )
    return images
