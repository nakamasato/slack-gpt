# Development

## Local

Set the environment variables `.env`

```
SLACK_BOT_TOKEN=
SIGNING_SECRET=
OPENAI_ORGANIZATION=
OPENAI_API_KEY=
```

Install

```
poetry install
```

Run

```
poetry run python slack_gpt/main.py
```

Check

```
curl -H 'Content-Type: application/json' -X POST -d '{"type": "url_verification", "challenge": "test"}' localhost:8080/slack/events
{
  "challenge": "test"
}
```
