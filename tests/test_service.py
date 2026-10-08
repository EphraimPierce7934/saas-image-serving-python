import pytest
from io import BytesIO
from urllib.error import HTTPError

from src.saas_image_service import ImageRequest, ImageServingService, InfraiClient, InfraiError, Tenant


class FakeClient:
    def upload(self, image):
        return {"id": "img-123"}

    def compress(self, image_id, request_id):
        return {"id": image_id, "status": "ready"}


def test_inactive_tenant_is_rejected_before_api_calls():
    service = ImageServingService(FakeClient())
    with pytest.raises(ValueError, match="active"):
        service.optimize_for_serving(Tenant("t1", "Trial"), ImageRequest("t1", "a.png", b"x"))


def test_active_tenant_handoff_returns_compressed_image():
    result = ImageServingService(FakeClient()).optimize_for_serving(
        Tenant("t1", "Trial", active=True), ImageRequest("t1", "a.png", b"x")
    )
    assert result == {"id": "img-123", "status": "ready"}


def test_http_error_business_envelope_is_typed(monkeypatch):
    def reject(req, timeout):
        raise HTTPError(req.full_url, 422, "Rejected", {}, BytesIO(b'{"ok":false,"error":{"code":"INVALID_IMAGE"}}'))

    monkeypatch.setattr("src.saas_image_service.request.urlopen", reject)
    with pytest.raises(InfraiError) as caught:
        InfraiClient(api_key="test").compress("image-1", "compress-1")
    assert caught.value.code == "INVALID_IMAGE"
    assert caught.value.status == 422
