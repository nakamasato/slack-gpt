import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from flask import Flask, request, jsonify
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

app = Flask(__name__)

# Slack Appの設定
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SIGNING_SECRET = os.environ["SIGNING_SECRET"]
VERIFIER = SignatureVerifier(SIGNING_SECRET)

client = WebClient(token=SLACK_BOT_TOKEN)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    # リクエストがSlackからのものであることを確認
    if not VERIFIER.is_valid_request(request.data, request.headers):
        return "Invalid request", 403

    # リトライの場合は何もしない
    if request.headers.get("x-slack-retry-num"):
        print("retry called")
        return {"statucCode": 200}

    # Slackからのイベントを取得
    data = request.get_json()
    event = data.get("event", {})

    # url_verification イベントの場合
    if data["type"] == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    # メッセージがボットによるメンションかどうかを確認
    if event.get("type") == "app_mention":
        # メンションされたチャンネルとユーザーを取得
        channel_id = event.get("channel")
        user_id = event.get("user")
        text = event.get("text")

        # メッセージをスレッドに返信
        try:
            response = client.reactions_add(
                channel=channel_id,
                timestamp=event["ts"],
                name="eye",
            )
            print(response)
            answer = ask_ai(text)
            client.chat_postMessage(
                channel=channel_id,
                text=f"{answer}",
                thread_ts=event["ts"]  # スレッドに返信
            )
            response = client.reactions_add(
                channel=channel_id,
                timestamp=event["ts"],
                name="white_check_mark",
            )
        except SlackApiError as e:
            response = client.reactions_add(
                channel=channel_id,
                timestamp=event["ts"],
                name="man-bowing",
            )
            client.chat_postMessage(
                channel=channel_id,
                text="Sorry. Something's wrong.",
                thread_ts=event["ts"]  # スレッドに返信
            )

    return jsonify({"success": True})


def ask_ai(text):
    chat = ChatOpenAI(
        model="gpt-3.5-turbo",
        streaming=False,
        verbose=True,
    )
    result = chat([HumanMessage(content=text)])  # AIMessageChunk
    return result.content

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
