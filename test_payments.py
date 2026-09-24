from uuid import uuid4

import pytest


def assert_payments(api, body, expected_count):
    response = api(
        "GET", "/debug/payments",
        params={"beneficiary_ref": body["beneficiary_ref"]},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["count"] == expected_count, data
    assert len(data["payments"]) == expected_count, data
    return data["payments"]


def test_health(api):
    response = api("GET", "/health")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}


def test_debug_requires_beneficiary_ref(api):
    response = api("GET", "/debug/payments")
    assert response.status_code == 400, response.text


def test_idempotent_retry(api, payment_body, headers, created_payment):
    retry = api("POST", "/v1/payments", json=payment_body, headers=headers)
    payments = assert_payments(api, payment_body, 1)
    assert retry.status_code == 200, retry.text
    assert retry.json()["payment_id"] == created_payment["payment_id"]
    assert payments[0]["payment_id"] == created_payment["payment_id"]


def test_idempotency_conflict(api, payment_body, headers, created_payment):
    changed_body = {**payment_body, "amount": 50000}
    conflict = api("POST", "/v1/payments", json=changed_body, headers=headers)
    payments = assert_payments(api, payment_body, 1)
    assert conflict.status_code == 409, conflict.text
    assert payments[0]["payment_id"] == created_payment["payment_id"]


def test_different_keys_create_independent_payments(
    api, payment_body, headers, created_payment
):
    second = api(
        "POST", "/v1/payments", json=payment_body,
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert_payments(api, payment_body, 2)
    assert second.status_code == 201, second.text
    assert created_payment["payment_id"] != second.json()["payment_id"]


def test_retry_after_fail_after_create(api, payment_body, headers):
    failed = api(
        "POST", "/v1/payments", json=payment_body,
        headers={**headers, "X-Simulate": "fail-after-create"},
    )
    assert failed.status_code == 500, failed.text
    before_retry = assert_payments(api, payment_body, 1)
    retry = api("POST", "/v1/payments", json=payment_body, headers=headers)
    assert_payments(api, payment_body, 1)
    assert retry.status_code == 200, retry.text
    assert retry.json()["payment_id"] == before_retry[0]["payment_id"]


def test_missing_idempotency_key_creates_nothing(api, payment_body):
    response = api("POST", "/v1/payments", json=payment_body)
    assert_payments(api, payment_body, 0)
    assert response.status_code == 400, response.text


@pytest.mark.parametrize(
    ['field', 'value'],
    [
        pytest.param("amount", 0, id="zero value"),
        pytest.param("amount", -1, id="negative value "),
        pytest.param("currency", "XXX", id="unsupported-currency"),
    ],
)
def test_invalid_body_creates_nothing(
    api, payment_body, headers, field, value,
):
    payment_body[field] = value
    response = api("POST", "/v1/payments", json=payment_body, headers=headers)
    assert_payments(api, payment_body, 0)
    assert response.status_code == 422, response.text


def test_get_created_payment(api, payment_body, created_payment):
    payment_id = created_payment["payment_id"]
    response = api("GET", f"/v1/payments/{payment_id}")
    assert_payments(api, payment_body, 1)
    assert response.status_code == 200, response.text
    assert response.json()["payment_id"] == payment_id, response.text
