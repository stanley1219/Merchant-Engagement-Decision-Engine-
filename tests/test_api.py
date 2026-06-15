from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.cache.redis_client import redis_client
from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _mock_lifespan_deps() -> Any:
    with (
        patch("src.main.init_db", new_callable=AsyncMock),
        patch("src.main.close_db", new_callable=AsyncMock),
        patch("src.main.redis_client.connect", new_callable=AsyncMock),
        patch("src.main.redis_client.disconnect", new_callable=AsyncMock),
    ):
        yield


@pytest.fixture
def _setup_redis_mock() -> Any:
    redis_client._client = MagicMock()
    redis_client._client.ping = AsyncMock(return_value=True)
    redis_client._client.keys = AsyncMock(return_value=[])
    redis_client._client.set = AsyncMock(return_value=True)
    redis_client.get = AsyncMock()
    redis_client.set = AsyncMock()
    redis_client.delete = AsyncMock()
    redis_client.exists = AsyncMock()
    redis_client.keys = AsyncMock(return_value=[])
    yield


class TestHealthEndpoint:
    def test_healthz_returns_healthy(self, client: TestClient) -> None:
        with (
            patch("src.api.v1.routes.health.get_session") as mock_session,
        ):
            redis_client._client = MagicMock()
            redis_client._client.ping = AsyncMock(return_value=True)
            mock_session.return_value.__aenter__.return_value.execute = AsyncMock()
            response = client.get("/v1/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "database" in data["dependencies"]
        assert "redis" in data["dependencies"]

    def test_healthz_db_unhealthy(self, client: TestClient) -> None:
        with (
            patch("src.api.v1.routes.health.get_session") as mock_session,
        ):
            redis_client._client = MagicMock()
            redis_client._client.ping = AsyncMock(return_value=True)
            mock_session.return_value.__aenter__.return_value.execute = AsyncMock(
                side_effect=Exception("DB down")
            )
            response = client.get("/v1/healthz")
        assert response.status_code == 200
        assert response.json()["dependencies"]["database"] == "unhealthy"


class TestMetadataEndpoint:
    def test_metadata_returns_capabilities(self, client: TestClient) -> None:
        response = client.get("/v1/metadata")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Vera Message Engine"
        assert "dentist" in data["categories"]
        assert "pharmacy" in data["categories"]
        assert "message_composition" in data["capabilities"]
        assert "max_message_length" in data["limits"]


class TestContextEndpoint:
    def test_upsert_merchant_context(self, client: TestClient) -> None:
        payload: dict[str, Any] = {
            "scope": "merchant",
            "context_id": "merchant-123",
            "version": 1,
            "payload": {
                "identity": {
                    "name": "Test Merchant",
                    "phone": "+919999999999",
                    "category": "dentist",
                    "locality": "Andheri",
                },
                "offers": [],
            },
            "delivered_at": datetime.now(UTC).isoformat(),
        }
        with patch("src.api.v1.routes.context.merchant_repo.upsert", new_callable=AsyncMock) as mock_upsert:
            mock_upsert.return_value = {"identity": {"merchant_id": "merchant-123"}}
            response = client.post("/v1/context", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is True
        assert "ack_id" in data

    def test_upsert_invalid_scope_returns_422(self, client: TestClient) -> None:
        payload: dict[str, Any] = {
            "scope": "unknown_scope",
            "context_id": "test",
            "version": 1,
            "payload": {},
            "delivered_at": datetime.now(UTC).isoformat(),
        }
        response = client.post("/v1/context", json=payload)
        assert response.status_code == 422

    def test_upsert_bad_type_scope_returns_422(self, client: TestClient) -> None:
        payload: dict[str, Any] = {
            "scope": 123,
            "context_id": "test",
            "version": 1,
            "payload": {},
            "delivered_at": datetime.now(UTC).isoformat(),
        }
        response = client.post("/v1/context", json=payload)
        assert response.status_code == 422


class TestTickEndpoint:
    def test_tick_merchant_not_found(self, client: TestClient, _setup_redis_mock: Any) -> None:
        redis_client.get = AsyncMock(return_value=None)
        response = client.post(
            "/v1/tick",
            json={"merchant_id": "nonexistent", "max_actions": 5},
        )
        assert response.status_code == 404

    def test_tick_returns_empty_actions(self, client: TestClient, _setup_redis_mock: Any) -> None:
        redis_client.get = AsyncMock(
            return_value={
                "identity": {"merchant_id": "m1", "name": "Test"},
                "category": "dentist",
                "offers": [],
                "performance": {},
            }
        )
        redis_client.client.keys = AsyncMock(return_value=[])
        response = client.post(
            "/v1/tick",
            json={"merchant_id": "m1", "max_actions": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["merchant_id"] == "m1"
        assert isinstance(data["actions"], list)

    def test_tick_invalid_category_returns_400(self, client: TestClient, _setup_redis_mock: Any) -> None:
        redis_client.get = AsyncMock(
            return_value={
                "identity": {"merchant_id": "m1", "name": "Test"},
                "category": "extraterrestrial",
                "offers": [],
                "performance": {},
            }
        )
        response = client.post(
            "/v1/tick",
            json={"merchant_id": "m1", "max_actions": 5},
        )
        assert response.status_code == 400

    def test_tick_force_flag_passed_through(self, client: TestClient, _setup_redis_mock: Any) -> None:
        redis_client.get = AsyncMock(
            side_effect=[
                {
                    "identity": {"merchant_id": "m1", "name": "Test"},
                    "category": "dentist",
                    "offers": [],
                    "performance": {},
                },
                {
                    "type": "review_request",
                    "payload": {},
                },
            ]
        )
        redis_client.client.keys = AsyncMock(return_value=["trigger:m1:t1"])
        redis_client.client.set = AsyncMock(return_value=True)
        response = client.post(
            "/v1/tick",
            json={"merchant_id": "m1", "max_actions": 5, "force": True},
        )
        assert response.status_code == 200
        assert response.json()["processed_triggers"] >= 0

    def test_tick_validates_max_actions_range(self, client: TestClient) -> None:
        response = client.post(
            "/v1/tick",
            json={"merchant_id": "m1", "max_actions": 100},
        )
        assert response.status_code == 422
        response = client.post(
            "/v1/tick",
            json={"merchant_id": "m1", "max_actions": 0},
        )
        assert response.status_code == 422


class TestReplyEndpoint:
    def test_reply_opt_out(self, client: TestClient) -> None:
        response = client.post(
            "/v1/reply",
            json={
                "merchant_id": "m1",
                "customer_id": "c1",
                "content": "stop",
                "intent": None,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["next_action"] == "suppress"
        assert data["updated_context"]["consent"]["sms"] is False

    def test_reply_explicit_intent(self, client: TestClient) -> None:
        response = client.post(
            "/v1/reply",
            json={
                "merchant_id": "m1",
                "customer_id": "c1",
                "content": "This is great",
                "intent": "interested",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["next_action"] == "notify_merchant"

    def test_reply_complaint(self, client: TestClient) -> None:
        response = client.post(
            "/v1/reply",
            json={
                "merchant_id": "m1",
                "customer_id": "c1",
                "content": "I have a complaint about the service",
                "intent": None,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["next_action"] == "escalate"
        assert data["updated_context"]["intent"] == "complaint"

    def test_reply_unknown_intent(self, client: TestClient) -> None:
        response = client.post(
            "/v1/reply",
            json={
                "merchant_id": "m1",
                "customer_id": "c1",
                "content": "Lorem ipsum dolor sit amet",
                "intent": None,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["next_action"] == "acknowledge"
        assert data["updated_context"]["intent"] == "unknown"


class TestRouteRegistration:
    def test_unknown_route_returns_404(self, client: TestClient) -> None:
        response = client.get("/v1/nonexistent")
        assert response.status_code == 404

    def test_health_route_registered(self, client: TestClient) -> None:
        response = client.get("/v1/healthz")
        assert response.status_code == 200

    def test_metadata_route_registered(self, client: TestClient) -> None:
        response = client.get("/v1/metadata")
        assert response.status_code == 200
