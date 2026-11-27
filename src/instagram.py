"""Publish images to Instagram using the official Meta Instagram Graph API."""

from __future__ import annotations

import time
import requests

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


def _wait_for_container(
    container_id: str,
    access_token: str,
    timeout_seconds: int = 60,
    poll_interval: float = 3.0,
) -> None:
    """Poll container status until Meta finishes fetching and processing the image."""
    deadline = time.monotonic() + timeout_seconds
    url = f"{GRAPH_API_BASE}/{container_id}"

    while time.monotonic() < deadline:
        response = requests.get(
            url,
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        status = data.get("status_code")

        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram media container failed: {data}")

        time.sleep(poll_interval)

    raise TimeoutError(f"Timed out waiting for Instagram container {container_id}")


def publish_photo(
    ig_user_id: str,
    access_token: str,
    image_url: str,
    caption: str,
) -> str:
    """Create a media container, wait for processing, and publish it to Instagram."""
    if not ig_user_id or not access_token:
        raise ValueError("IG_USER_ID and IG_ACCESS_TOKEN are required to post.")

    create_resp = requests.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    create_resp.raise_for_status()
    creation_id = create_resp.json().get("id")
    if not creation_id:
        raise RuntimeError(f"Failed to create media container: {create_resp.text}")

    _wait_for_container(creation_id, access_token)

    publish_resp = requests.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    publish_resp.raise_for_status()
    media_id = publish_resp.json().get("id")
    if not media_id:
        raise RuntimeError(f"Failed to publish media container: {publish_resp.text}")
    return str(media_id)
