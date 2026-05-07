"""
Pytest fixtures for CI smoke tests.
Uses FastAPI TestClient (in-process, no live server needed).
"""
import os
import sys
import pytest

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from server import app

    with TestClient(app) as c:
        yield c
