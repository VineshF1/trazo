"""Photo quality check.

A blurry, dark, washed-out or very small photo is not sent to the model. The user
is asked to take it again, which is cheaper and more honest than reading a photo
that cannot be read.

All thresholds are starting guesses in config.py and must be tuned on real photos.
"""

import io
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.config import (
    BLUR_MIN_VARIANCE,
    BRIGHTNESS_MAX,
    BRIGHTNESS_MIN,
    MIN_IMAGE_SIDE,
)


@dataclass(frozen=True)
class QualityResult:
    """What the check measured, and whether the photo should be retaken."""

    ok: bool
    blur_variance: float
    brightness: float
    width: int
    height: int
    problems: list[str] = field(default_factory=list)

    @property
    def retake_message(self) -> str:
        """One plain sentence. Never "Oops", and never a guess at the content."""
        if not self.problems:
            return ""
        if len(self.problems) == 1:
            return f"Take the photo again: {self.problems[0]}."
        joined = "; ".join(self.problems[:-1]) + f"; and {self.problems[-1]}"
        return f"Take the photo again: {joined}."


def check_quality(image_bytes: bytes) -> QualityResult:
    """Measure blur, brightness and size. Rotation is fixed first, as in the pipeline."""
    with Image.open(io.BytesIO(image_bytes)) as opened:
        image = ImageOps.exif_transpose(opened)
        grey = image.convert("L")
        width, height = grey.size
        pixels = np.asarray(grey, dtype=np.uint8)

    blur_variance = float(cv2.Laplacian(pixels, cv2.CV_64F).var())
    brightness = float(pixels.mean())

    problems: list[str] = []
    if min(width, height) < MIN_IMAGE_SIDE:
        problems.append(
            f"the page is too small ({width}x{height}, and it should be at least "
            f"{MIN_IMAGE_SIDE} px on the short side)"
        )
    if blur_variance < BLUR_MIN_VARIANCE:
        problems.append("it is too blurry, so hold the phone still")
    if brightness < BRIGHTNESS_MIN:
        problems.append("it is too dark, so use more light")
    elif brightness > BRIGHTNESS_MAX:
        problems.append("it is washed out, so move out of direct glare")

    return QualityResult(
        ok=not problems,
        blur_variance=round(blur_variance, 1),
        brightness=round(brightness, 1),
        width=width,
        height=height,
        problems=problems,
    )
