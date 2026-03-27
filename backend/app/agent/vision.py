"""Process images for Claude's vision API."""

import base64
import io

from PIL import Image

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_DIMENSION = 2048


def process_image(image_bytes: bytes, mime_type: str) -> dict:
    """
    Process an image for the Anthropic vision API.
    Resizes if too large and returns an Anthropic image content block.
    """
    # Resize if needed
    if len(image_bytes) > MAX_IMAGE_SIZE:
        image_bytes = _resize_image(image_bytes, mime_type)

    encoded = base64.standard_b64encode(image_bytes).decode("utf-8")

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": mime_type,
            "data": encoded,
        },
    }


def _resize_image(image_bytes: bytes, mime_type: str) -> bytes:
    """Resize image to fit within limits while maintaining aspect ratio."""
    img = Image.open(io.BytesIO(image_bytes))

    # Calculate resize ratio
    ratio = min(MAX_DIMENSION / max(img.size), 1.0)
    if ratio < 1.0:
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Save to bytes
    output = io.BytesIO()
    fmt = "PNG" if mime_type == "image/png" else "JPEG"
    img.save(output, format=fmt, quality=85)
    return output.getvalue()


def build_vision_messages(
    text_content: str,
    images: list[tuple[bytes, str]],
) -> list[dict]:
    """
    Build message content blocks combining text and images.

    Args:
        text_content: The text portion of the message
        images: List of (image_bytes, mime_type) tuples

    Returns:
        List of content blocks for the Anthropic API
    """
    content = []

    # Add images first
    for image_bytes, mime_type in images:
        content.append(process_image(image_bytes, mime_type))

    # Add text
    content.append({"type": "text", "text": text_content})

    return content
