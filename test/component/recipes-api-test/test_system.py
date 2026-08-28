# test/backend/recipes-api-test/test_system.py


# ============================================================
# Liveness probe - API process is reachable
# ============================================================

def test_health_probe(base_url, api_session):
    response = api_session.get(
        f"{base_url}/system/health"
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["status"] == "healthy"


# ============================================================
# Readiness probe - API can reach required dependencies
# ============================================================

def test_readiness_probe(base_url, api_session):
    response = api_session.get(
        f"{base_url}/system/ready"
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["status"] == "ready"


# ============================================================
# Startup probe - application completed startup successfully
# ============================================================

def test_startup_probe(base_url, api_session):
    response = api_session.get(
        f"{base_url}/system/startup"
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["status"] == "started"