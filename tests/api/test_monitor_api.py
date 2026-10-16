def test_health_check_returns_name_and_version(client):
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json() == {"name": "TEST APP", "version": "9.9.9"}


def test_unknown_route_returns_router_not_found(client):
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"trace_id": "middleware-001", "message": "router not found"}
