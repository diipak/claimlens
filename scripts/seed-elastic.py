import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers

# Resolve paths
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
database_dir = root_dir / "database"

# Load backend environment variables
dotenv_path = backend_dir / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()

def seed_elastic():
    print("=" * 60)
    print("CLAIMLENS - ELASTICSEARCH SEEDING TOOL")
    print("=" * 60)

    # 1. Retrieve credentials
    es_url = os.getenv("ES_URL")
    es_api_key = os.getenv("ES_API_KEY")

    if not es_url or not es_api_key:
        print("ERROR: Elastic credentials not found in environment!")
        print("Please configure ES_URL and ES_API_KEY in your backend/.env file.")
        print("\nSetup Guide:")
        print("1. Create an Elasticsearch Serverless deployment on GCP (Elastic Cloud).")
        print("2. Copy your URL endpoint (e.g., https://my-deployment.es.us-central1.gcp.elastic-cloud.com).")
        print("3. Generate an API Key under Kibana -> Stack Management -> API Keys.")
        print("4. Paste them into backend/.env")
        sys.exit(1)

    print(f"Connecting to Elasticsearch instance at: {es_url}")
    try:
        es = Elasticsearch(es_url, api_key=es_api_key)
        if not es.ping():
            print("ERROR: Could not ping Elasticsearch. Please check your URL and API Key.")
            sys.exit(1)
        print("Successfully connected to Elasticsearch!")
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")
        sys.exit(1)

    # 2. Read curated sources
    sources_path = database_dir / "curated_sources.json"
    if not sources_path.exists():
        print(f"ERROR: Curated sources seed file not found at: {sources_path}")
        sys.exit(1)

    with open(sources_path, "r") as f:
        documents = json.load(f)

    print(f"Loaded {len(documents)} documents from {sources_path.name}.")

    # 3. Create or recreate index with custom mappings for semantic keyword retrieval
    index_name = "curated-sources"
    
    # Check if index already exists
    if es.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists.")
        # Ask or just recreate to ensure fresh clean state
        print(f"Recreating index '{index_name}' to ensure clean seed state...")
        es.indices.delete(index=index_name)

    # Simple index mappings optimized for factual queries
    mappings = {
        "mappings": {
            "properties": {
                "title": {"type": "text", "analyzer": "english"},
                "domain": {"type": "keyword"},
                "tier": {"type": "integer"},
                "date": {"type": "date", "format": "yyyy-MM-dd"},
                "url": {"type": "keyword"},
                "content": {"type": "text", "analyzer": "english"},
                "snippet": {"type": "text", "analyzer": "english"},
                "scenarioTag": {"type": "keyword"}
            }
        }
    }

    try:
        es.indices.create(index=index_name, body=mappings)
        print(f"Created index '{index_name}' with optimized mappings.")
    except Exception as e:
        print(f"ERROR: Failed to create index: {e}")
        sys.exit(1)

    # 4. Bulk Indexing
    print("Indexing documents...")
    actions = []
    for idx, doc in enumerate(documents):
        actions.append({
            "_index": index_name,
            "_id": str(idx + 1),
            "_source": doc
        })

    try:
        success_count, failed = helpers.bulk(es, actions)
        print(f"Successfully indexed {success_count} documents into '{index_name}'.")
        if failed:
            print(f"WARNING: {len(failed)} indexing actions failed: {failed}")
    except Exception as e:
        print(f"ERROR: Bulk indexing failed: {e}")
        sys.exit(1)

    print("=" * 60)
    print("SEEDING COMPLETE. ClaimLens is ready for Demo Mode!")
    print("=" * 60)

if __name__ == "__main__":
    seed_elastic()
