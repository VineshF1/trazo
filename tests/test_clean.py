"""Photo quality check tests. Generated images only.

The images are built so that the measured quantity is not a guess: a unsharp
pattern gives a high Laplacian variance, a flat image gives a low one, and a dark
or bright fill gives a low or high mean.
"""

import io

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw

from app.clean import check_quality
from app.config import BLUR_MIN_VARIANCE, BRIGHTNESS_MAX, BRIGHTNESS_MIN, MIN_IMAGE_SIDE


def _encode(array: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(array, mode="L").convert("RGB").save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def _flat(value: int, size=(1200, 1600)) -> bytes:
    return _encode(np.full((size[1], size[0]), value, dtype=np.uint8))


def _textured(size=(1200, 1600), ink=0, paper=255) -> bytes:
    """High-contrast strokes on paper: sharp enough to be measured as in focus.

    Built to look like a page of writing, because a flat rectangle is correctly
    measured as blurry (zero Laplacian variance) and a clean white page has a mean
    grey around 218, not around 128.
    """
    image = Image.new("L", size, paper)
    draw = ImageDraw.Draw(image)
    step = max(30, size[1] // 40)
    width = max(3, size[1] // 300)
    y = step
    while y < size[1] - step:
        draw.line([(step, y), (size[0] - step, y)], fill=ink, width=width)
        draw.line([(step, y + width * 4), (size[0] - step * 3, y + width * 4)], fill=ink, width=max(2, width - 1))
        y += step
    return _encode(np.asarray(image))


def _blurred(size=(1200, 1600)) -> bytes:
    image = Image.open(io.BytesIO(_textured(size))).convert("L")
    blurred = cv2.GaussianBlur(np.asarray(image), (101, 101), 0)
    return _encode(blurred)


def test_a_sharp_and_well_lit_photo_passes():
    result = check_quality(_textured())
    assert result.ok is True
    assert result.problems == []
    assert result.blur_variance >= BLUR_MIN_VARIANCE


def test_a_blurry_photo_is_rejected_with_a_retake_message():
    result = check_quality(_blurred())
    assert result.ok is False
    assert "blurry" in result.retake_message


def test_a_dark_photo_is_rejected():
    result = check_quality(_flat(10))
    assert result.ok is False
    assert "dark" in result.retake_message
    assert result.brightness < BRIGHTNESS_MIN


def test_a_washed_out_photo_is_rejected():
    result = check_quality(_flat(252))
    assert result.ok is False
    assert "washed out" in result.retake_message
    assert result.brightness > BRIGHTNESS_MAX


def test_a_small_photo_is_rejected():
    result = check_quality(_textured(size=(300, 400)))
    assert result.ok is False
    assert "too small" in result.retake_message
    assert min(result.width, result.height) < MIN_IMAGE_SIDE


def test_a_photo_failing_two_checks_reports_both():
    result = check_quality(_blurred(size=(300, 400)))
    assert result.ok is False
    assert len(result.problems) == 2
    assert "too small" in result.retake_message
    assert "blurry" in result.retake_message


def test_the_result_reports_the_measurements():
    result = check_quality(_textured(size=(800, 1000)))
    assert (result.width, result.height) == (800, 1000)
    assert result.brightness > 0
    assert isinstance(result.blur_variance, float)


def test_exif_rotation_is_applied_before_measuring():
    image = Image.fromarray(np.asarray(Image.open(io.BytesIO(_textured(size=(400, 1200))))))
    exif = Image.Exif()
    exif[274] = 6
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=95, exif=exif)
    result = check_quality(buffer.getvalue())
    assert result.width > result.height  # stored sideways, measured upright


def test_a_threshold_can_be_tuned_without_touching_the_check(monkeypatch):
    import app.clean as clean

    monkeypatch.setattr(clean, "MIN_IMAGE_SIDE", 5000)
    assert clean.check_quality(_textured()).ok is False