#!/bin/bash
# Exit on error
set -e

PROJECT_ID="dataagentplatform"
REGION="europe-west3"
SERVICE_NAME="claimlens"

echo "=========================================================="
echo "Deploying ClaimLens to Cloud Run ($REGION) in $PROJECT_ID..."
echo "=========================================================="

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,REASONING_MODEL=gemini-2.5-flash,ES_URL=https://claimlens-001-c39714.es.us-central1.gcp.elastic.cloud,ES_API_KEY=YzVnVmlwNEJudkRieURVSDZvNkY6ZDBfMDg3dXN3VFN0S3dBc1BHMVR3dw==,BRAVE_API_KEY=BSAmpOAqd1ISygG5ScUuZ767zGKQnR8"

echo "=========================================================="
echo "Deployment completed successfully!"
echo "=========================================================="
