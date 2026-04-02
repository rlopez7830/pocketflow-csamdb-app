"""Image identity utility.

Manages backend-generated image IDs and an in-memory TTL-backed cache
that maps image_id to resolved image metadata and file paths.
"""

import logging
import threading
import time
import uuid

logger = logging.getLogger(__name__)

_IMAGE_CACHE = {}
_CACHE_LOCK = threading.Lock()
_TTL_SECONDS = 30 * 60  # 30 minutes


def assign_image_ids(matched_images):
    """Assign unique image IDs and store mappings in the in-memory cache.

    Args:
        matched_images: A list of dicts with keys file_name, absolute_path,
            source_directory.

    Returns:
        A list of enriched dicts with additional keys: image_id, image_url,
        status, message.
    """
    _cleanup_expired()
    enriched = []
    with _CACHE_LOCK:
        for img in matched_images:
            image_id = f"img_{uuid.uuid4().hex[:12]}"
            entry = {
                "image_id": image_id,
                "file_name": img["file_name"],
                "absolute_path": img["absolute_path"],
                "source_directory": img["source_directory"],
                "image_url": f"/image/{image_id}",
                "status": "ready",
                "message": "Image is available for display.",
                "created_at": time.time(),
            }
            _IMAGE_CACHE[image_id] = entry
            enriched.append(entry)

    logger.info("Assigned %d image IDs", len(enriched))
    return enriched


def resolve_image_by_id(image_id):
    """Look up a cached image record by its image_id.

    Args:
        image_id: The backend-generated image identifier.

    Returns:
        A dict with image metadata if found and not expired, or None.
    """
    _cleanup_expired()
    with _CACHE_LOCK:
        entry = _IMAGE_CACHE.get(image_id)
        if entry is None:
            logger.warning("Image ID not found: %s", image_id)
            return None
        if time.time() - entry["created_at"] > _TTL_SECONDS:
            del _IMAGE_CACHE[image_id]
            logger.warning("Image ID expired: %s", image_id)
            return None
        return dict(entry)


def _cleanup_expired():
    """Remove expired entries from the cache."""
    now = time.time()
    with _CACHE_LOCK:
        expired = [k for k, v in _IMAGE_CACHE.items()
                   if now - v["created_at"] > _TTL_SECONDS]
        for k in expired:
            del _IMAGE_CACHE[k]
    if expired:
        logger.info("Cleaned up %d expired image cache entries", len(expired))
