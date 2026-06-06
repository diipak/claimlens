# ClaimLens

ClaimLens is a mobile-first responsive web application built for the **Google Cloud Rapid Agent Hackathon**. It provides an evidence-first, single-claim fact-checking pipeline designed to verify numeric, ranking, and temporal claims from pasted text or screenshots using the **Vertex AI Gemini API** and **Elasticsearch**.

---

## Architecture

- **Frontend:** React + Vite + TypeScript (inside `/frontend`). High-contrast, editorial/data-audit design optimized for mobile dimensions.
- **Backend:** A lightweight FastAPI server (inside `/backend`) that orchestrates screenshot OCR (multimodal Gemini), claim extraction, search query generation, evidence retrieval, and verification reasoning.
- **Retrieval Layer:** Official Elastic Integration via MCP / elasticsearch client querying curated source indices. Includes a built-in token-matching local fallback simulator for offline testing.

---

## Quick Start Setup

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- Google Cloud CLI authenticated (Application Default Credentials):
  ```bash
  gcloud auth application-default login
  ```

---

### 1. Backend Setup

1. Navigate to `/backend`:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file inside `/backend` with your credentials:
   ```env
   GOOGLE_CLOUD_PROJECT=dataagentplatform
   GOOGLE_CLOUD_LOCATION=us-central1
   REASONING_MODEL=gemini-2.5-flash  # or gemini-2.5-pro

   # Elastic Configuration (Required for Demo Mode, optional for Dev Fallback)
   ES_URL=https://your-elastic-deployment.es.us-central1.gcp.elastic-cloud.com
   ES_API_KEY=your-api-key-here
   ```
5. Start the backend server:
   ```bash
    python main.py
    ```
    The backend will run at `http://0.0.0.0:8000`.

---

### 2. Frontend Setup

1. Navigate to `/frontend`:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
   The frontend will run at `http://localhost:5173`. Open this URL and toggle Mobile Emulation (iPhone viewports) in Chrome DevTools.

---

## Setting up Elastic Cloud (GCP)

To run the application in its primary, spec-compliant **Demo Mode**, you must connect it to a real Elasticsearch index:

1. **Create an Elastic Cloud Account:** Go to [Elastic Cloud](https://cloud.elastic.co/) and create a deployment (select Google Cloud as the provider).
2. **Retrieve Credentials:** Copy your **Elasticsearch Endpoint URL** and generate an **API Key** under Kibana Developer Tools or API Keys management.
3. **Configure Environment:** Add `ES_URL` and `ES_API_KEY` to `backend/.env`.
4. **Seed the Curated Index:**
   Before querying, index the records inside `database/curated_sources.json` into an Elasticsearch index named `curated-sources`. You can do this using Kibana Dev Tools or by running a script:
   ```bash
   # Example Kibana Dev Tools request:
   POST /curated-sources/_bulk
   { "index": { "_id": "1" } }
   { "title": "GCP Infrastructure Alpha Metro Expansion Report 2026", "domain": "Department of Transportation", "tier": 1, ... }
   ```

---

## Automated Validation Test

To verify that the verification pipeline, Gemini agents, and search fallbacks are operational, run:

```bash
python scripts/test-scenarios.py
```
This script queries the backend's `/api/verify` endpoint with test cases for Scenario 1, Scenario 2, and Scenario 3, asserting that response schemas are strictly validated and outputting verification reports.
