import hmac
import json
import os
import time

import pytest
from slack_sdk.signature import SignatureVerifier

# from unittest.mock import patch


VERIFIER = SignatureVerifier(os.environ["SIGNING_SECRET"])


@pytest.fixture()
def app():
    from slack_gpt.main import app

    app.config.update(
        {
            "TESTING": True,
        }
    )
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


# @patch("langchain_openai.ChatOpenAI")
def test_request_example_invalid(client):
    response = client.post("/slack/events")
    assert response.status_code == 403
    assert response.get_data(as_text=True) == "Invalid request"


def test_request_example(client):
    signing_secret = "test_signing_secret"
    os.environ["SIGNING_SECRET"] = signing_secret
    timestamp = str(int(time.time()))
    data = {
        "type": "url_verification",
        "challenge": "challenge",
    }
    signature = VERIFIER.generate_signature(timestamp=timestamp, body=json.dumps(data))
    print(f"{signature=}, {json.dumps(data).encode()=}")
    assert VERIFIER.is_valid(
        body=json.dumps(data), timestamp=timestamp, signature=signature
    )
    headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
        "Content-Type": "application/json",
    }
    response = client.post(
        "/slack/events",
        data=json.dumps(data),
        # json=data, # The Content-Type header will be set to application/json automatically.
        headers=headers,
    )
    print(response)
    assert hmac.compare_digest(
        signature,
        VERIFIER.generate_signature(timestamp=timestamp, body=json.dumps(data)),
    )
    assert VERIFIER.is_valid_request(body=json.dumps(data), headers=headers)
    assert response.status_code == 200
