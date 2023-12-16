import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from flask import Flask, request, jsonify

app = Flask(__name__)

# Slack Appの設定
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
# SIGNING_SECRET = os.environ["SIGNING_SECRET"]
# VERIFIER = SignatureVerifier(SIGNING_SECRET)

client = WebClient(token=SLACK_BOT_TOKEN)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    # リクエストがSlackからのものであることを確認
    # if not VERIFIER.is_valid_request(request.data, request.headers):
    #     return "Invalid request", 403

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

        # メッセージをスレッドに返信
        try:
            response = client.chat_postMessage(
                channel=channel_id,
                text=f"Hello <@{user_id}>!",
                thread_ts=event["ts"]  # スレッドに返信
            )
            print(response)
        except SlackApiError as e:
            print(f"Error posting message: {e.response['error']}")

    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
