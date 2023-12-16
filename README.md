# slack-automation

## Slack Bot setting

1. Crete a Slack bot https://api.slack.com/apps/
1. [URL verification](https://api.slack.com/events/url_verification)
1. Configure Event Subscriptions
    - Request URL: https://xxxxx/slack/events
    - Subscribe to bot events: `app_mention`, `chat:write`

## Local

```
poetry install
```

```
SLACK_BOT_TOKEN=xxx poetry run gunicorn --bind :8080 slack_automation.main:app
```


```
curl -H 'Content-Type: application/json' -X POST -d '{"type": "url_verification", "challenge": "test"}' localhost:8080/slack/events
{
  "challenge": "test"
}
```

## Deploy to Cloud RUn

```
PROJECT=xxxx
REGION=asia-northeast1
SA_NAME=slack-automation
```

```
poetry export -f requirements.txt --output requirements.txt
```

```
gcloud iam service-accounts create $SA_NAME --project $PROJECT
```

```
gcloud secrets create slack-bot-token --replication-policy automatic --project $PROJECT
echo -n "xoxb-xxx" | gcloud secrets versions add slack-bot-token --data-file=- --project $PROJECT
gcloud secrets add-iam-policy-binding slack-bot-token \
    --member="serviceAccount:${SA_NAME}@${PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --project ${PROJECT}
```

build

```
gcloud builds submit . --pack "image=$REGION-docker.pkg.dev/$PROJECT/cloud-run-source-deploy/slack-automation" --project ${PROJECT}
```

<details><summary>initial deploy</summary>

```
gcloud run deploy slack-automation \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account ${SA_NAME}@${PROJECT}.iam.gserviceaccount.com \
    --set-secrets=SLACK_BOT_TOKEN=slack-bot-token:latest \
    --project ${PROJECT}
```

```
gcloud run services describe slack-automation --format export --project $PROJECT --region $REGION > service.yaml
```

</details>

```
gcloud run services replace service.yaml --project $PROJECT --region $REGION
```

```
URL=$(gcloud run services describe slack-automation --project $PROJECT --region ${REGION} --format json | jq -r .status.url)
```

check

```
curl -H 'Content-Type: application/json' -X POST -d '{"type": "url_verification", "challenge": "test"}' $URL/slack/events
{"challenge": "test"}
```

## Ref

- https://slack.dev/bolt-python/tutorial/getting-started
