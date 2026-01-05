# RAG Chat with Langflow and OpenSearch

A Retrieval-Augmented Generation (RAG) chat system using Langflow's visual interface with OpenSearch as the vector store. Build your RAG flows visually and deploy a beautiful chat interface.

## Features

- **Chat Interface**: Modern Next.js UI to interact with your RAG system
- **Langflow Integration**: Visual drag-and-drop RAG flow builder
- **OpenSearch Vector Store**: Hybrid search with BM25 + semantic vectors
- **Document Ingestion**: Use Langflow's visual interface to ingest documents
- **Hybrid Search**: Combines semantic search with keyword matching for better results

## Prerequisites

- Docker Desktop (for OpenSearch)
- Python 3.9+ (for Langflow)
- Node.js 18+ (for the chat UI)
- API keys: OpenAI or IBM watsonx.ai

Verify installations:
```bash
docker --version
python --version
node --version
```

---

## Quick Start

### 1. Start OpenSearch

```bash
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:9200
```

### 2. Set Up Python Environment

Create a virtual environment and install Langflow:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install uv
uv pip install --upgrade langflow
uv pip install fastapi==0.123.6  # Required compatibility fix
```

### 3. Set Environment Variables

```bash
# Choose your LLM provider:

# Option 1: IBM watsonx.ai
export WATSONX_API_KEY="your-api-key"
export WATSONX_PROJECT_ID="your-project-id"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"

# Option 2: OpenAI
export OPENAI_API_KEY="your-openai-api-key"
```

### 4. Create OpenSearch Index

Create the index with proper vector field configuration:

```bash
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
```

> **Note**: Dimension 1536 matches OpenAI's `text-embedding-3-small` model. Adjust if using a different embedding model.

### 5. Start Langflow

```bash
langflow run
```

Open http://localhost:7860 in your browser.

### 6. Import the Pre-built Flow

1. In Langflow, click **My Projects** → **New Project** → **Import**
2. Select `RAG with Opensearch.json` from this repo
3. Update the OpenSearch Vector Store component:
   - **OpenSearch URL**: `http://localhost:9200`
   - **Index Name**: Your index name (default: `hybrid_demo`)
   - **Embedding Model**: Must match your indexed documents
4. Add your API keys (OpenAI or watsonx)
5. Test the flow with a sample query
6. Copy the Flow ID from the URL or Settings panel

The flow includes Chat Input, OpenSearch retrieval, RAG prompt, and LLM response components pre-configured.

---

## Using Your Existing OpenSearch Index

If you already have documents indexed in OpenSearch, you can easily connect the chat UI to your existing index.

### Configure Langflow to Use Your Index

1. Open Langflow at http://localhost:7860
2. Open your imported RAG flow (or create a new one)
3. Find the **OpenSearch Vector Store** component in the flow
4. Update the following settings:
   - **Index Name**: Change from `hybrid_demo` to your index name (e.g., `my_documents`)
   - **OpenSearch URL**: Ensure it's set to `http://localhost:9200`
   - **Embedding Model**: Must match the model used during ingestion
5. Save the flow

### Required Index Schema

Your OpenSearch index should have these fields:

```json
{
  "mappings": {
    "properties": {
      "vector_field": {
        "type": "knn_vector",
        "dimension": 1536  // Must match your embedding model
      },
      "text": {
        "type": "text"
      },
      "metadata": {
        "type": "object"
      }
    }
  }
}
```

### Verify Your Index

Check that your index exists and has documents:

```bash
# List all indices
curl http://localhost:9200/_cat/indices?v

# Check document count
curl http://localhost:9200/YOUR_INDEX_NAME/_count

# View a sample document
curl http://localhost:9200/YOUR_INDEX_NAME/_search?size=1
```

### Important Notes

- **Embedding Dimensions**: The vector dimension in your index must match the embedding model in Langflow (default: 1536 for OpenAI text-embedding-3-small)
- **Field Names**: Langflow expects `vector_field` for vectors and `text` for content by default
- **Multiple Indices**: You can create multiple Langflow flows, each connected to different indices

---

## Alternative: Python Ingestion Script

If you prefer to use a Python script for document ingestion instead of an external solution, we provide a ready-to-use ingestion script.

### Setup

1. **Install Python dependencies**:

```bash
pip install -r requirements.txt
```

2. **Configure environment variables**:

Copy `env-example.txt` to `.env` and add your API keys:

```bash
# OpenSearch Configuration
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_INDEX=hybrid_demo

# Unstructured.io API (for document processing)
UNSTRUCTURED_API_KEY=your_unstructured_api_key_here

# OpenAI API (for embeddings)
OPENAI_API_KEY=your_openai_api_key_here
```

3. **Get API Keys**:
   - **Unstructured.io**: Sign up at https://unstructured.io/ for document parsing
   - **OpenAI**: Get your API key from https://platform.openai.com/

### Usage

Run the ingestion script with your documents directory:

```bash
python scripts/ingest_unstructured_opensearch.py --input-dir ./data
```

**Options**:
- `--input-dir`: Directory containing documents (default: `./data/demo_docs`)
- `--index-name`: OpenSearch index name (default: `hybrid_demo`)
- `--recreate-index`: Delete and recreate the index before ingestion

**Supported file types**: PDF, DOCX, TXT, MD, HTML

### What the Script Does

1. **Document Processing**: Uses Unstructured.io API to extract text from various document formats
2. **Text Chunking**: Splits documents into 1000-character chunks with 200-character overlap
3. **Embedding Generation**: Creates vector embeddings using OpenAI's `text-embedding-3-small` model
4. **Indexing**: Stores chunks with embeddings in OpenSearch with hybrid search configuration

### Verify Ingestion

```bash
# Check document count
curl http://localhost:9200/hybrid_demo/_count

# View sample documents
curl http://localhost:9200/hybrid_demo/_search?size=3
```

---

## RAG Chat UI

A Next.js web interface is available in the `frontend/` directory.

### Setup

```bash
cd frontend
npm install
cp env-example.txt .env.local
# Edit .env.local with your LANGFLOW_FLOW_ID
```

Your `.env.local` should contain:
```bash
LANGFLOW_URL=http://localhost:7860
LANGFLOW_FLOW_ID=your-flow-id-from-langflow
LANGFLOW_API_KEY=your-api-key  # If authentication is enabled
```

### Run

```bash
npm run dev
```

Open http://localhost:3000

---

## Building RAG Flows in Langflow

### Basic RAG Query Flow

1. **Chat Input** - User's question
2. **OpenSearch Vector Store** - Retrieves relevant chunks (k=5)
3. **Prompt Template** - Combines context with question
4. **LLM** - Generates the answer
5. **Chat Output** - Displays response

### Recommended Prompt Template

```
You are a helpful assistant that answers questions based on the provided context.

Context:
{context}

Question: {question}

Rules:
- Only use information from the context above
- If the context doesn't contain the answer, say so
- Cite sources when possible
- Be concise but thorough

Answer:
```

### Hybrid Search Flow (Advanced)

For better results, combine semantic search with keyword matching. The pre-built flow includes:

1. Extract keywords from the user's question using an LLM
2. Run three parallel searches:
   - **Vector search**: Semantic similarity
   - **BM25 search**: Exact text matching
   - **Boosted field search**: Keywords and titles (3x and 2x boost)
3. Fusion combines all results

See the pre-built `RAG with Opensearch.json` flow for a complete example.

---

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Chat UI** | http://localhost:3000 | Chat interface |
| **Langflow** | http://localhost:7860 | Visual flow builder |
| **OpenSearch** | http://localhost:9200 | Vector store API |

---

## OpenSearch Commands

### Basic Commands

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f opensearch

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

### Verify OpenSearch

```bash
curl http://localhost:9200
curl http://localhost:9200/_cat/indices?v
curl http://localhost:9200/hybrid_demo/_count
```

### Query Examples

```bash
# Search all documents
curl -X GET "http://localhost:9200/hybrid_demo/_search" -H 'Content-Type: application/json' -d'
{
  "size": 10,
  "query": {"match_all": {}}
}
'

# Text search
curl -X GET "http://localhost:9200/hybrid_demo/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match": {"text": "your search term"}}
}
'

# Delete all documents (keeps index structure)
curl -X POST "http://localhost:9200/hybrid_demo/_delete_by_query" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}}
}
'
```

---

## LLM Configuration

### IBM watsonx.ai

```bash
export WATSONX_API_KEY="your-api-key"
export WATSONX_PROJECT_ID="your-project-id"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"
```

Recommended models:
- `ibm/granite-13b-chat-v2` for general Q&A
- `meta-llama/llama-3-70b-instruct` for complex reasoning

### OpenAI

```bash
export OPENAI_API_KEY="your-api-key"
```

---

## Troubleshooting

**SSL Error: `[SSL] record layer failure`**

Langflow is trying HTTPS but local OpenSearch uses HTTP. Ensure your URL is `http://localhost:9200` (not `https://`).

**`nmslib engine is deprecated`**

OpenSearch 3.x removed the nmslib engine. Pre-create the index with `faiss` engine as shown in Step 4.

**`Field 'vector_field' is not knn_vector type`**

The index was created with the wrong configuration. Delete it and recreate:
```bash
curl -X DELETE "http://localhost:9200/hybrid_demo"
# Then run the create index command from Step 4
```

**`vm.max_map_count [65530] is too low`**

OpenSearch needs more virtual memory. On macOS:
```bash
docker run -it --privileged --pid=host debian nsenter -t 1 -m -u -n -i sh
sysctl -w vm.max_map_count=262144
exit
docker-compose up -d
```

**Langflow startup errors with FastAPI**

Downgrade FastAPI: `uv pip install fastapi==0.123.6`

**Langflow authentication error**

Since Langflow v1.5+, authentication is required. Either:
1. Get an API key from Langflow Settings → API Keys
2. Or start Langflow with: `LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true langflow run`

**Frontend can't connect to Langflow**

- Verify Langflow is running: http://localhost:7860
- Check `LANGFLOW_FLOW_ID` in `.env.local` matches your flow
- Ensure Langflow API key is set if authentication is enabled

---

## Tips

- Start with a basic RAG flow before adding hybrid search complexity
- Use OpenSearch queries to verify documents are indexed correctly
- Adjust chunk sizes (default 1000 chars with 200 overlap) based on your document types
- For hybrid search, use a fast LLM like gpt-4o-mini for keyword extraction
- Extract fewer keywords (1-3) for better precision
- Test document ingestion with a few files before processing large batches

---

## Resources

- [Langflow Documentation](https://docs.langflow.org/)
- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [OpenSearch Hybrid Search](https://opensearch.org/docs/latest/search-plugins/hybrid-search/)
- [watsonx.ai Documentation](https://www.ibm.com/docs/en/watsonx-as-a-service)
