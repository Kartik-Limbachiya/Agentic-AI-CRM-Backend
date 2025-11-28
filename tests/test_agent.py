from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Verify that the health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "active", "service": "agentic-crm-backend"}

# Note: Testing the /campaign/run endpoint requires a valid API Key.
# In a real CI/CD, we would mock the LLM calls so we don't need real keys.