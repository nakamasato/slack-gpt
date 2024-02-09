import json
import os
import time
from unittest.mock import patch

import pytest
from slack_sdk.signature import SignatureVerifier

VERIFIER = SignatureVerifier(os.environ["SIGNING_SECRET"])
EVENT_PATH = "/slack/events"


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
def headers(timestamp):
    def generate_headers(data: str | bytes):
        return {
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": VERIFIER.generate_signature(
                timestamp=timestamp, body=data
            ),
            "Content-Type": "application/json",
        }

    return generate_headers


# @patch("langchain_openai.ChatOpenAI")
def test_request_example_invalid(flask_cli):
    response = flask_cli.post(EVENT_PATH)
    assert response.status_code == 403
    assert response.get_data(as_text=True) == "Invalid request"


def test_url_verification(flask_cli, headers):
    """
    url_verification
    https://github.com/nakamasato/slack-gpt/blob/695d6ca73ae65629be29f9d8159c26fdb2c7a815/tests/test_main.py#L44-L74
    """
    data_str: str = json.dumps(
        {
            "type": "url_verification",
            "challenge": "challenge",
        }
    )

    response = flask_cli.post(
        EVENT_PATH,
        data=data_str,  # json=data or json=json.dumps(data) doesn't work
        headers=headers(data=data_str),
    )
    assert response.status_code == 200
    assert response.get_json()["challenge"] == "challenge"


@patch("slack_gpt.main.slack")
def test_message(slack_mock, flask_cli, headers):
    """
    when receiving message event
    add reaction
    """
    data_str: str = json.dumps(
        {
            "type": "message",
            "event": {
                "channel": "C000000",  # set in DEDICATED_CHANNELS
                "ts": "1707454484.055569",
            },
        }
    )

    response = flask_cli.post(
        EVENT_PATH,
        data=data_str,  # json=data or json=json.dumps(data) doesn't work
        headers=headers(data=data_str),
    )
    assert response.status_code == 200
    slack_mock.reactions_add.assert_called_with(
        channel="C000000",
        timestamp="1707454484.055569",
        name="eye",
    )
