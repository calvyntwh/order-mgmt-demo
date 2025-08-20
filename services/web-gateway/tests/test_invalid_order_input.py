from fastapi.testclient import TestClient

from app.main import app as gateway_app


def test_submit_order_invalid_quantity() -> None:
    client = TestClient(gateway_app)
    # submit form with non-numeric quantity
    r = client.post(
        "/order",
        data={"item_name": "Widget", "quantity": "abc", "notes": "x"},
    )
    assert r.status_code == 400
    assert "Invalid input" in r.text
