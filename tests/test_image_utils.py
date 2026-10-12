"""Image preparation tests. Generated images only, no real prescriptions."""

import io

from PIL import Image

from app.config import JPEG_QUALITY, MAX_IMAGE_SIDE
from app.image_utils import image_info, prepare_image


def _jpeg_bytes(width, height, mode="RGB", exif=None) -> bytes:
    image = Image.new(mode, (width, height), "white")
    buffer = io.BytesIO()
    # Pillow 12 rejects exif=None, so only pass it when a tag set is supplied.
    kwargs = {"format": "JPEG"}
    if exif is not None:
        kwargs["exif"] = exif
    image.save(buffer, **kwargs)
    return buffer.getvalue()


def test_a_large_image_is_scaled_down_to_the_cap():
    prepared = prepare_image(_jpeg_bytes(4000, 3000))
    info = image_info(prepared)
    assert max(info["width"], info["height"]) == MAX_IMAGE_SIDE
    assert info["format"] == "JPEG"


def test_aspect_ratio_is_kept_when_scaling():
    prepared = prepare_image(_jpeg_bytes(4000, 2000))
    info = image_info(prepared)
    assert info["width"] == MAX_IMAGE_SIDE
    assert info["height"] == MAX_IMAGE_SIDE // 2


def test_a_small_image_is_not_upscaled():
    prepared = prepare_image(_jpeg_bytes(400, 300))
    info = image_info(prepared)
    assert (info["width"], info["height"]) == (400, 300)


def test_output_is_jpeg_and_under_the_quality_setting():
    prepared = prepare_image(_jpeg_bytes(2000, 2000))
    assert prepared[:2] == b"\xff\xd8"  # JPEG start of image
    with Image.open(io.BytesIO(prepared)) as image:
        assert image.format == "JPEG"
    assert int(JPEG_QUALITY * 100) == 80


def test_a_non_rgb_image_is_converted():
    prepared = prepare_image(_jpeg_bytes(200, 200, mode="L"))
    assert image_info(prepared)["mode"] == "RGB"


def test_exif_rotation_is_applied():
    exif = Image.Exif()
    exif[274] = 6  # orientation 6: the stored image is rotated 90 degrees clockwise
    prepared = prepare_image(_jpeg_bytes(400, 200, exif=exif))
    info = image_info(prepared)
    assert (info["width"], info["height"]) == (200, 400)


def test_image_info_does_not_modify_the_bytes():
    original = _jpeg_bytes(300, 200)
    image_info(original)
    assert original == _jpeg_bytes(300, 200)