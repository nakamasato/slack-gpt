# slack-gpt

Slack GPT integration

<img src="docs/slack.png" width="400">

## Slack Bot setting

1. Create a Slack bot https://api.slack.com/apps/
1. Grant permission to the bot (`chat:write`, `app_mentions:read`, `channels:history`, `reactions:read`, `reactions:write`)
1. Configure Event Subscriptions
    - Request URL: https://xxxxx/slack/events (This URL will be available after deploy to GCP Cloud Run) [ref](https://api.slack.com/events/url_verification)
    - Subscribe to bot events: `app_mention`

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

## Deploy to GCP Cloud Run

### 1. Set environment variables

```
PROJECT=xxxx
REGION=asia-northeast1
SA_NAME=slack-gpt
```

### 2. Generate `requirements.txt`

```
poetry export -f requirements.txt --output requirements.txt
```

### 3. Create service account

```
gcloud iam service-accounts create $SA_NAME --project $PROJECT
```

### 4. Create Secrets and grant permission to the service account

```bash
# slack bot token
gcloud secrets create slack-bot-token --replication-policy automatic --project $PROJECT
echo -n "xoxb-xxx" | gcloud secrets versions add slack-bot-token --data-file=- --project $PROJECT
gcloud secrets add-iam-policy-binding slack-bot-token \
    --member="serviceAccount:${SA_NAME}@${PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --project ${PROJECT}

# slack signing secret
gcloud secrets create slack-signing-secret --replication-policy automatic --project $PROJECT
echo -n "xxx" | gcloud secrets versions add slack-signing-secret --data-file=- --project $PROJECT
gcloud secrets add-iam-policy-binding slack-signing-secret \
    --member="serviceAccount:${SA_NAME}@${PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --project ${PROJECT}

# openai organization
gcloud secrets create openai-organization --replication-policy automatic --project $PROJECT
echo -n "xxx" | gcloud secrets versions add openai-organization --data-file=- --project $PROJECT
gcloud secrets add-iam-policy-binding openai-organization \
    --member="serviceAccount:${SA_NAME}@${PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --project ${PROJECT}

# openai api key
gcloud secrets create openai-api-key --replication-policy automatic --project $PROJECT
echo -n "xxx" | gcloud secrets versions add openai-api-key --data-file=- --project $PROJECT
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:${SA_NAME}@${PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --project ${PROJECT}
```

### 5. Build and deploy to Cloud Run

```
gcloud run deploy slack-gpt \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account ${SA_NAME}@${PROJECT}.iam.gserviceaccount.com \
    --set-secrets=SLACK_BOT_TOKEN=slack-bot-token:latest \
    --set-secrets=SIGNING_SECRET=slack-signing-secret:latest \
    --set-secrets=OPENAI_ORGANIZATION=openai-organization:latest \
    --set-secrets=OPENAI_API_KEY=openai-api-key:latest \
    --project ${PROJECT}
```

<details><summary>deploy with yaml</summary>

```
gcloud builds submit . --pack "image=$REGION-docker.pkg.dev/$PROJECT/cloud-run-source-deploy/slack-gpt:$(date '+%Y%m%d%H%M%S')" --project ${PROJECT}
```

Get yaml

```
gcloud run services describe slack-gpt --format export --project $PROJECT --region $REGION > service.yaml
```

Deploy with yaml

```
gcloud run services replace service.yaml --project $PROJECT --region $REGION
```

</details>

### 6. Get Cloud Run URL

```
URL=$(gcloud run services describe slack-gpt --project $PROJECT --region ${REGION} --format json | jq -r .status.url)
```

### [7. Configure Slack Event Subscriptions](https://api.slack.com/apis/connections/events-api)

Use this `${URL}/slack/events` for Slack Event Subscriptions.

<img src="docs/slack-event-subscriptions-config.png" width="400">

Choose `app_mention` in **Subscribe to bot events** section

<img src="docs/slack-event-subscriptions-bot-events.png" width="400">

### 8. Check

Check with curl

```
curl -H 'Content-Type: application/json' -X POST -d '{"type": "url_verification", "challenge": "test"}' $URL/slack/events
{"challenge": "test"}
```

Check with Slack

<img src="docs/slack.png" width="400">

## Ref

- https://slack.dev/bolt-python/tutorial/getting-started
- [Slack Event retries](https://api.slack.com/apis/connections/events-api#retries)
