"""
API endpoint tests for the trading agent backend
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client):
    """Test root endpoint returns system info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Goldrix"
    assert "version" in data
    assert data["symbol"] == "XAUUSD"


def test_health_check(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["symbol"] == "XAUUSD"


def test_dashboard_endpoint(client):
    """Test dashboard returns all required data"""
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()

    # Check all required fields
    assert "status" in data
    assert "price" in data
    assert "account" in data
    assert "positions" in data
    assert "signal" in data

    # Validate data types
    assert isinstance(data["positions"], list)
    assert "balance" in data["account"]
    assert "equity" in data["account"]


def test_account_endpoint(client):
    """Test account info endpoint"""
    response = client.get("/api/account")
    assert response.status_code == 200
    data = response.json()

    assert "balance" in data
    assert "equity" in data
    assert "margin" in data
    assert "open_positions" in data
    assert data["account_type"] in ["demo", "real"]


def test_positions_endpoint(client):
    """Test positions endpoint returns list"""
    response = client.get("/api/positions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_price_endpoint(client):
    """Test current price endpoint"""
    response = client.get("/api/price")
    assert response.status_code == 200
    data = response.json()

    if data:  # May be None if not connected
        assert "close" in data
        assert "open" in data
        assert "high" in data
        assert "low" in data


def test_signal_endpoint(client):
    """Test trading signal endpoint"""
    response = client.get("/api/signal")
    assert response.status_code == 200


class TestTradingOperations:
    """Test trading operations"""

    def test_open_position_buy(self, client):
        """Test opening a buy position"""
        response = client.post("/api/positions/open", json={
            "symbol": "XAUUSD",
            "type": "buy",
            "volume": 0.01
        })
        # Should succeed or return error if not enough margin
        assert response.status_code in [200, 400]

    def test_open_position_sell(self, client):
        """Test opening a sell position"""
        response = client.post("/api/positions/open", json={
            "symbol": "XAUUSD",
            "type": "sell",
            "volume": 0.01
        })
        assert response.status_code in [200, 400]

    def test_close_all_positions(self, client):
        """Test closing all positions"""
        response = client.post("/api/positions/close-all")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_endpoint(self, client):
        """Test 404 on invalid endpoint"""
        response = client.get("/api/invalid-endpoint")
        assert response.status_code == 404

    def test_invalid_position_type(self, client):
        """Test error on invalid position type"""
        response = client.post("/api/positions/open", json={
            "symbol": "XAUUSD",
            "type": "invalid",
            "volume": 0.01
        })
        assert response.status_code == 422  # Validation error
