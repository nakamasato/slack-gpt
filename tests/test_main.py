import json
import os
import time
from unittest.mock import patch

import pytest
from slack_sdk.signature import SignatureVerifier

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
def flask_cli(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture(scope="session")
def timestamp():
    return str(int(time.time()))


@pytest.fixture()
def generate_signature(timestamp):
    def generate_signature_from_data(data):
        return VERIFIER.generate_signature(timestamp=timestamp, body=json.dumps(data))

    return generate_signature_from_data


# @patch("langchain_openai.ChatOpenAI")
def test_request_example_invalid(flask_cli):
    response = flask_cli.post("/slack/events")
    assert response.status_code == 403
    assert response.get_data(as_text=True) == "Invalid request"


def test_url_verification(flask_cli, timestamp, generate_signature):
    """
    url_verification
    https://github.com/nakamasato/slack-gpt/blob/695d6ca73ae65629be29f9d8159c26fdb2c7a815/tests/test_main.py#L44-L74
    """
    data = {
        "type": "url_verification",
        "challenge": "challenge",
    }

    response = flask_cli.post(
        "/slack/events",
        data=json.dumps(data),  # json=data or json=json.dumps(data) doesn't work
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": generate_signature(data=data),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.get_json()["challenge"] == "challenge"


@patch("slack_gpt.main.slack")
def test_message(slack_mock, flask_cli, timestamp, generate_signature):
    """
    when receiving message event
    add reaction
    """
    data = {
        "type": "message",
        "event": {
            "channel": "C000000",  # set in DEDICATED_CHANNELS
            "ts": "1707454484.055569",
        },
    }

    response = flask_cli.post(
        "/slack/events",
        data=json.dumps(data),  # json=data or json=json.dumps(data) doesn't work
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": generate_signature(data=data),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    slack_mock.reactions_add.assert_called_with(
        channel="C000000",
        timestamp="1707454484.055569",
        name="eye",
    )
