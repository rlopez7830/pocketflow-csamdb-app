"""Image resize utility.

Resizes a PNG image proportionally to fit within configured maximum
dimensions without upscaling.
"""

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)

MAX_WIDTH = 1600
MAX_HEIGHT = 1200


def resize_image(png_bytes, max_width=MAX_WIDTH, max_height=MAX_HEIGHT):
    """Resize a PNG proportionally without upscaling.

    Args:
        png_bytes: Raw PNG image bytes.
        max_width: Maximum allowed width in pixels.
        max_height: Maximum allowed height in pixels.

    Returns:
        A tuple of (resized_png_bytes, mime_type).
    """
    img = Image.open(io.BytesIO(png_bytes))
    original_width, original_height = img.size

    if original_width <= max_width and original_height <= max_height:
        logger.info("Image %dx%d fits within %dx%d, no resize needed",
                     original_width, original_height, max_width, max_height)
        return png_bytes, "image/png"

    ratio = min(max_width / original_width, max_height / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="PNG")
    resized_bytes = output.getvalue()

    logger.info("Resized image from %dx%d to %dx%d",
                original_width, original_height, new_width, new_height)
    return resized_bytes, "image/png"
