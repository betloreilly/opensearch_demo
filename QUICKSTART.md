# Quick Start Guide

Get your RAG chat system running in 5 steps.

## Step 1: Start OpenSearch

```bash
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:9200
```

You should see JSON output with OpenSearch version info.

## Step 2: Set Up Python & Langflow

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Langflow
pip install uv
uv pip install --upgrade langflow
uv pip install fastapi==0.123.6
```

## Step 3: Configure Environment

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"

# Or for IBM watsonx:
export WATSONX_API_KEY="your-api-key"
export WATSONX_PROJECT_ID="your-project-id"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"
```

## Step 4: Create Index & Start Langflow

```bash
# Create OpenSearch index
curl -X PUT "http://localhost:9200/hybrid_demo" -H 'Content-Type: application/json' -d '
{
  "settings": { "index": { "knn": true } },
  "mappings": {
    "properties": {
      "vector_field": {
        "type": "knn_vector",
        "dimension": 1536,
        "method": { "name": "hnsw", "space_type": "cosinesimil", "engine": "faiss" }
      },
      "text": { "type": "text" },
      "metadata": { "type": "object", "enabled": true }
    }
  }
}
'

# Start Langflow
langflow run
```

Open http://localhost:7860 and:
1. Click **My Projects** → **Import**
2. Select `RAG with Opensearch.json`
3. Update OpenSearch connection to `http://localhost:9200`
4. Add your OpenAI API key
5. Copy your Flow ID from the URL or Settings

## Step 5: Configure Your Index & Start Chat UI

### Option A: Use Your Existing OpenSearch Index

In Langflow, configure the OpenSearch Vector Store component:
1. Open your imported flow
2. Find the **OpenSearch Vector Store** component
3. Set **Index Name** to your existing index (e.g., `my_documents`)
4. Ensure **Embedding Model** matches your indexed documents
5. Test the flow with a sample query

### Option B: Use Python Ingestion Script

If you need to ingest documents, use the provided Python script:

```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env file with API keys
cp env-example.txt .env
# Edit .env and add UNSTRUCTURED_API_KEY and OPENAI_API_KEY

# Run ingestion
python scripts/ingest_unstructured_opensearch.py --input-dir ./data
```

See the main README for detailed ingestion instructions.

### Start Chat UI

```bash
# In a new terminal
cd frontend
npm install

# Create .env.local
cp env-example.txt .env.local

# Edit .env.local and add your Langflow Flow ID:
# LANGFLOW_FLOW_ID=your-flow-id-here

# Start the app
npm run dev
```

Open http://localhost:3000 and start chatting!

## Verify Everything Works

- ✅ OpenSearch: http://localhost:9200
- ✅ Langflow: http://localhost:7860
- ✅ Chat UI: http://localhost:3000

## Troubleshooting

**Port already in use?**
```bash
# Check what's using the port
lsof -i :3000  # or :7860, :9200

# Stop the process or change ports in configs
```

**Langflow won't start?**
```bash
# Downgrade FastAPI
pip install fastapi==0.123.6
```

**Langflow authentication error?**
```bash
# Start without auth
export LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true
langflow run
```

**Chat UI won't connect?**
- Verify Langflow is running at http://localhost:7860
- Check your `LANGFLOW_FLOW_ID` in `.env.local`
- Make sure the flow is properly configured in Langflow

**No documents found?**
- Use the Python ingestion script (see Step 5, Option B)
- Or configure Langflow to use your existing index (see Step 5, Option A)
- Check documents exist: `curl http://localhost:9200/hybrid_demo/_count`
