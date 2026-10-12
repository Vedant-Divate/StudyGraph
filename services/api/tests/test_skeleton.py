"""Phase 0 API tests (mock backends only)."""

from fastapi.testclient import TestClient

from app.llm.mock_provider import CANNED_REFUSAL, MockProvider
from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "llm_provider" in body
    # No secrets may ever leak through the health endpoint.
    assert "api_key" not in body
    assert "secret" not in "".join(body.keys()).lower()


def test_mock_provider_refusal_fixture() -> None:
    provider = MockProvider()
    result = provider.complete_structured(
        prompt="off-material: refuse this", schema={"type": "object"}, model="mock-1"
    )
    assert result.data["segments"][0]["label"] == "not_covered"
    assert CANNED_REFUSAL in result.data["segments"][0]["text"]


def test_mock_provider_vision_fixture() -> None:
    provider = MockProvider()
    description = provider.vision_describe(
        image_path="page-1.png", prompt="describe", model="mock-1"
    )
    assert "page-1.png" in description
