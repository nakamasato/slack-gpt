import os

from flask import Flask, jsonify, request
from langchain.globals import set_llm_cache
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from langchain_community.cache import InMemoryCache
from langchain_core.messages import HumanMessage

# from slack_gpt.libs.tools import ask_ai

# Read from environment variables
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SIGNING_SECRET = os.environ["SIGNING_SECRET"]
DEDICATED_CHANNELS = os.getenv("DEDICATED_CHANNELS", "").split(
    ","
)  # Also send to the channel in the dedicated channels
VERIFIER = SignatureVerifier(SIGNING_SECRET)
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

# Client
app = Flask(__name__)
set_llm_cache(InMemoryCache())
slack = WebClient(token=SLACK_BOT_TOKEN)
chat = (
    ChatOpenAI(
        model=GPT_MODEL,
        streaming=False,
        verbose=True,
    )
    if GPT_MODEL.startswith("gpt")
    else ChatGoogleGenerativeAI(model=GPT_MODEL, verbose=True)
)


@app.route("/slack/events", methods=["POST"])
def slack_events():
    # Check if the request from Slack
    if not VERIFIER.is_valid_request(request.data, request.headers):
        return "Invalid request", 403

    # skip for slack retry
    if request.headers.get("x-slack-retry-num"):
        print("retry called")
        return {"statucCode": 200}

    # get event data
    data = request.get_json()
    event = data.get("event", {})

    # for url_verification event
    if data["type"] == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    channel_id = event.get("channel")
    # TODO: reply to message in the dedicated channel without mentioning
    if data["type"] == "message":
        if channel_id in DEDICATED_CHANNELS:
            slack.reactions_add(
                channel=channel_id,
                timestamp=event["ts"],
                name="eye",
            )

    # for app_mention event
    if event.get("type") == "app_mention":
        user_id = event.get("user")
        text = event.get("text")
        print(f"{channel_id=}, {user_id=}")

        # Reply message
        try:
            slack.reactions_add(
                channel=channel_id,
                timestamp=event["ts"],
                name="speech_balloon",
            )
            answer = ask_ai(chat, text)
            slack.chat_postMessage(
                channel=channel_id,
                text=f"{answer}",
                thread_ts=event["ts"],  # Reply in thread
                reply_broadcast=channel_id in DEDICATED_CHANNELS,
            )
            slack.reactions_add(
                channel=channel_id,
                timestamp=event["ts"],
                name="white_check_mark",
            )
        except SlackApiError:
            slack.reactions_add(
                channel=channel_id,
                timestamp=event["ts"],
                name="man-bowing",
            )
            slack.chat_postMessage(
                channel=channel_id,
                text="Sorry. Something's wrong.",
                thread_ts=event["ts"],  # Reply in thread
                reply_broadcast=channel_id in DEDICATED_CHANNELS,
            )

    return jsonify({"success": True})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


def ask_ai(chat, text):
    """ask LLM to answer the question"""
    result = chat.invoke(input=[HumanMessage(content=text)])
    return result.content


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
