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


def test_url_verification(client):
    timestamp = str(int(time.time()))
    data = {
        "type": "url_verification",
        "challenge": "challenge",
    }
    signature = VERIFIER.generate_signature(
        timestamp=timestamp, body=json.dumps(data).encode()
    )
    headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
        "Content-Type": "application/json",
    }
    response = client.post(
        "/slack/events",
        data=json.dumps(data),  # json=data or json=json.dumps(data) doesn't work
        headers=headers,
    )
    assert response.status_code == 200
    assert response.get_json()["challenge"] == "challenge"
