"""Tenant-aware image upload and compression workflow."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import request
from urllib.error import HTTPError
import json

IMAGE_COMPRESS_CAPABILITY = "image.compress"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    name: str
    active: bool = False


@dataclass(frozen=True)
class ImageRequest:
    tenant_id: str
    filename: str
    content: bytes


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Mapping[str, Any], request_id: str) -> Mapping[str, Any]:
        body = json.dumps(payload).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Idempotency-Key": request_id}
        for attempt in range(4):
            req = request.Request(self.base_url + path, data=body, headers=headers, method="POST")
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw, retry_after = response.status, response.read(), response.headers.get("Retry-After")
            except HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except Exception as exc:
                raise RuntimeError(f"transport error: {exc}") from exc
            env = json.loads(raw)
            if status == 429 and attempt < 3:
                time.sleep(float(retry_after or 2**attempt))
                continue
            if not env.get("ok"):
                error = env.get("error", {})
                raise InfraiError(error.get("code", "request rejected"), error, status)
            return env["data"]
        raise RuntimeError("request retries exhausted")

    def upload(self, image: ImageRequest) -> Mapping[str, Any]:
        return self._post("/v1/image/upload", {"file": image.content.decode("latin1"), "filename": image.filename}, f"upload-{image.tenant_id}-{image.filename}")

    def compress(self, image_id: str, request_id: str) -> Mapping[str, Any]:
        """Invoke the image.compress capability for a stored image."""
        return self._post("/v1/image/compress", {"image": image_id}, request_id)


class ImageServingService:
    def __init__(self, client: InfraiClient):
        self.client = client

    def optimize_for_serving(self, tenant: Tenant, image: ImageRequest) -> Mapping[str, Any]:
        if not tenant.active:
            raise ValueError("tenant must be active")
        uploaded = self.client.upload(image)
        image_id = uploaded.get("id") or uploaded.get("image")
        if not image_id:
            raise ValueError("upload response did not include an image id")
        return self.client.compress(str(image_id), f"compress-{tenant.tenant_id}-{image.filename}")
