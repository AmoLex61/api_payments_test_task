from uuid import uuid4

import pytest
import requests

BASE_URL = 'http://127.0.0.1:8080'


@pytest.fixture
def api():
    with requests.Session() as session:
        def request(method, path, **kwargs):
            return session.request(
                method, f"{BASE_URL}{path}", timeout=5, **kwargs
            )

        yield request


@pytest.fixture
def payment_body():
    return {
        "corridor": "RUB/THB",
        "amount": 100000,
        "currency": "RUB",
        "beneficiary_ref": f"ref-{uuid4().hex}",
    }


@pytest.fixture
def headers():
    return {"Idempotency-Key": uuid4().hex}


@pytest.fixture
def created_payment(api, payment_body, headers):
    response = api(
        "POST", "/v1/payments", json=payment_body, headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()
