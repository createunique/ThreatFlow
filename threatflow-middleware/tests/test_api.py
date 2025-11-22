"""API endpoint tests"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_analyzers():
    response = client.get("/api/analyzers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)