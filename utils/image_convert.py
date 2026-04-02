"""TIFF to PNG conversion utility.

Converts the first page of a TIFF image to PNG format for browser display.
"""

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def convert_tiff_first_page_to_png(tiff_bytes):
    """Convert the first page of a TIFF to PNG bytes.

    Args:
        tiff_bytes: Raw TIFF file bytes.

    Returns:
        PNG image bytes.
    """
    logger.info("Converting TIFF first page to PNG (%d input bytes)", len(tiff_bytes))
    img = Image.open(io.BytesIO(tiff_bytes))
    img.seek(0)

    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")

    output = io.BytesIO()
    img.save(output, format="PNG")
    png_bytes = output.getvalue()
    logger.info("Converted to PNG: %d bytes, size %s", len(png_bytes), img.size)
    return png_bytes
