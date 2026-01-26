from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_rates():
    response = client.get("/api/rates?currency=JPY&from_date=2026-01-22&to_date=2026-01-22")
    assert response.status_code == 200
    assert response.json() == [{"date": "2026-01-22", "rate": 158.79}]