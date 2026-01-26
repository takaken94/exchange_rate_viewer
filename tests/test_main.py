from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_rates():
    response = client.get("/api/rates?currency=JPY")
    assert response.status_code == 200
    assert response.json() == {"data": {"name": "Test"}}