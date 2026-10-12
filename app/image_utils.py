"""Image preparation for the model call.

Everything happens in memory. Nothing is written to disk, and no image data is
carried inside any error message.
"""

import io

from PIL import Image, ImageOps

from app.config import JPEG_QUALITY, MAX_IMAGE_SIDE


def prepare_image(image_bytes: bytes) -> bytes:
    """Fix EXIF rotation, convert to RGB, downscale, and return JPEG bytes.

    The longest side is capped at MAX_IMAGE_SIDE. An image already that small is
    returned unchanged: it is never upscaled.
    """
    with Image.open(io.BytesIO(image_bytes)) as opened:
        image = ImageOps.exif_transpose(opened)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image = _downscale(image, MAX_IMAGE_SIDE)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=int(JPEG_QUALITY * 100), optimize=True)
        return buffer.getvalue()


def image_info(image_bytes: bytes) -> dict:
    """Size, mode and format of an encoded image. Used for reporting, not for reading."""
    with Image.open(io.BytesIO(image_bytes)) as opened:
        return {
            "width": opened.width,
            "height": opened.height,
            "mode": opened.mode,
            "format": opened.format,
        }


def _downscale(image: Image.Image, longest_side: int) -> Image.Image:
    if max(image.size) <= longest_side:
        return image
    copy = image.copy()
    copy.thumbnail((longest_side, longest_side), Image.LANCZOS)
    return copy