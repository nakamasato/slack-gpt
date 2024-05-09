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

## Deploy to GCP Cloud Run

### 1. Set environment variables

```
PROJECT=xxxx
REGION=asia-northeast1
SA_NAME=slack-gpt
```

### 2. Generate `requirements.txt`

```
poetry export -f requirements.txt --output requirements.txt --without-hashes
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

