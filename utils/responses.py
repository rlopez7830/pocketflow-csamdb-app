"""Response builder utility.

Builds structured API response payloads for the lookup and image endpoints.
"""

import logging

logger = logging.getLogger(__name__)


def build_lookup_success(shared):
    """Build the success response for the /lookup endpoint.

    Args:
        shared: The shared store dict after the lookup flow completes.

    Returns:
        A dict representing the JSON response payload.
    """
    vid = shared["request"]["vid"]
    matched_images = shared["filesystem"].get("matched_images", [])

    # Derive unique source directories from matched images
    seen_dirs = set()
    directories = []
    for img in matched_images:
        d = img.get("source_directory", "")
        if d and d not in seen_dirs:
            seen_dirs.add(d)
            directories.append({"directory": d, "exists": True})

    images = [
        {
            "image_id": img["image_id"],
            "file_name": img["file_name"],
            "image_url": img["image_url"],
            "source_directory": img["source_directory"],
            "status": img.get("status", "ready"),
            "message": img.get("message", ""),
        }
        for img in matched_images
    ]

    count = len(images)
    message = f"{count} matching image file{'s' if count != 1 else ''} found."

    return {
        "vid": vid,
        "status": "success",
        "message": message,
        "manufacturing": {
            "aries_results": shared["manufacturing"].get("aries_results", []),
        },
        "directories": directories,
        "images": images,
    }


def build_lookup_error(vid, error_message):
    """Build an error response for the /lookup endpoint.

    Args:
        vid: The VID that was looked up.
        error_message: A user-facing error string.

    Returns:
        A dict representing the JSON error response payload.
    """
    return {
        "vid": vid,
        "status": "error",
        "message": error_message,
        "manufacturing": {},
        "directories": [],
        "images": [],
    }
