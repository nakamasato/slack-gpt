# slack-gpt

Slack GPT integration

Docker: [nakamasato/slack-gpt](https://hub.docker.com/r/nakamasato/slack-gpt)

<img src="docs/slack.png" width="400">

## Environment Varibales

- `SLACK_BOT_TOKEN`: Slack bot token
- `SIGNING_SECRET`: Slack signing secret
- `DEDICATED_CHANNELS` (optional): Dedicated channel for the bot
- `GPT_MODEL` (optional): GPT model (e.g. `gpt-3.5-turbo`, `gpt-4`, `gemini-pro`) (default: `gpt-3.5-turbo`)
- OpenAI
    - `OPENAI_ORGANIZATION`: OpenAI organization
    - `OPENAI_API_KEY`: OpenAI API key
- Gemini
    - `GOOGLE_API_KEY`: Google API key
        ```

> [!NOTE]
> If you use Gemini, you need to generate an API key.
> `gcloud services api-keys create --api-target=service=generativelanguage.service.com --display-name "Gemini API Key" --project $PROJECT`


## Create Slack app

1. Create a Slack app https://api.slack.com/apps/
1. Grant permission to the bot (`chat:write`, `app_mentions:read`, `channels:history`, `reactions:read`, `reactions:write`)
1. Configure Event Subscriptions
    - Request URL: https://xxxxx/slack/events (This URL will be available after deploy to GCP Cloud Run) [ref](https://api.slack.com/events/url_verification)
    - Subscribe to bot events: `app_mention`

## Deploy to GCP Cloud Run

### 1. Set environment variables

```
PROJECT=xxxx
REGION=asia-northeast1
SA_NAME=slack-gpt
```

### 2. Create service account

```
gcloud iam service-accounts create $SA_NAME --project $PROJECT
```

### 3. Create Secrets and grant permission to the service account

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

### 4. Deploy to Cloud Run

```
gcloud run deploy slack-gpt \
    --image nakamasato/slack-gpt:0.0.5 \
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

### 5. Get Cloud Run URL

```
URL=$(gcloud run services describe slack-gpt --project $PROJECT --region ${REGION} --format json | jq -r .status.url)
```

### [6. Configure Slack Event Subscriptions](https://api.slack.com/apis/connections/events-api)

Use this `${URL}/slack/events` for Slack Event Subscriptions.

<img src="docs/slack-event-subscriptions-config.png" width="400">

Choose `app_mention` in **Subscribe to bot events** section

<img src="docs/slack-event-subscriptions-bot-events.png" width="400">

### 7. Check

Check with curl

```
curl -H 'Content-Type: application/json' -X POST -d '{"type": "url_verification", "challenge": "test"}' $URL/slack/events
{"challenge": "test"}
```

Check on Slack

<img src="docs/slack.png" width="400">

## Ref

- https://slack.dev/bolt-python/tutorial/getting-started
- [Slack Event retries](https://api.slack.com/apis/connections/events-api#retries)
