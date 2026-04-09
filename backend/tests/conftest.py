"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, '/Users/hitler/Projects/gold-trading-agent/backend')

from main import app


@pytest.fixture
def client():
    """Synchronous test client"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_trading_service():
    """Mock trading service for testing"""
    class MockService:
        def __init__(self):
            self.state = type('State', (), {
                'connected': True,
                'is_trading': True,
                'symbol': 'XAUUSD',
                'error': None
            })()

        async def get_account_info(self):
            return {
                'balance': 10000.0,
                'equity': 10000.0,
                'margin': 0.0,
                'free_margin': 10000.0,
                'margin_level': 100.0,
                'open_positions': 0,
                'account_type': 'demo'
            }

        async def get_positions(self):
            return []

        async def get_price(self, symbol='XAUUSD'):
            return type('Price', (), {
                'close': 4821.0,
                'open': 4820.0,
                'high': 4825.0,
                'low': 4818.0,
                'volume': 100
            })()

    return MockService()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
