"""Upload generated quote images to a public URL for Instagram Graph API."""

from __future__ import annotations

import hashlib
from pathlib import Path
import time
import requests

from src.config import Settings

IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


def _upload_to_imgbb(image_path: Path, api_key: str, expiration_seconds: int = 600) -> str:
    """Upload image to ImgBB with short expiration and return its direct URL."""
    with image_path.open("rb") as fh:
        response = requests.post(
            IMGBB_UPLOAD_URL,
            params={"key": api_key, "expiration": expiration_seconds},
            files={"image": fh},
            timeout=30,
        )
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        raise RuntimeError(f"ImgBB upload failed: {data}")
    return str(data["data"]["url"])


def _upload_to_cloudinary(
    image_path: Path,
    cloud_name: str,
    api_key: str,
    api_secret: str,
) -> str:
    """Upload image to Cloudinary using signed upload and return secure_url."""
    timestamp = int(time.time())
    folder = "quote_posts"
    to_sign = f"folder={folder}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

    url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    with image_path.open("rb") as fh:
        response = requests.post(
            url,
            data={
                "api_key": api_key,
                "timestamp": timestamp,
                "folder": folder,
                "signature": signature,
            },
            files={"file": fh},
            timeout=30,
        )
    response.raise_for_status()
    data = response.json()
    if "secure_url" not in data:
        raise RuntimeError(f"Cloudinary upload failed: {data}")
    return str(data["secure_url"])


def upload_image(image_path: Path, settings: Settings) -> str:
    """Upload image to the configured host (ImgBB or Cloudinary)."""
    if settings.imgbb_api_key:
        return _upload_to_imgbb(image_path, settings.imgbb_api_key)

    if (
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    ):
        return _upload_to_cloudinary(
            image_path=image_path,
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
        )

    raise RuntimeError(
        "No image host configured. Set IMGBB_API_KEY or "
        "CLOUDINARY_CLOUD_NAME + CLOUDINARY_API_KEY + CLOUDINARY_API_SECRET."
    )
