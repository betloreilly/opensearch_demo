# RAG Chat with Langflow and OpenSearch

A Retrieval-Augmented Generation (RAG) chat system using Langflow's visual interface for preparing the RAG flow with OpenSearch as the vector store. Build your RAG flows visually and deploy a beautiful chat interface.

## Features

- **Chat Interface**: Modern Next.js UI to interact with your RAG system
- **Langflow Integration**: Visual drag-and-drop RAG flow builder
- **OpenSearch Vector Store**: Hybrid search with BM25 + semantic vectors
- **Document Ingestion**: You can use langflow or python script to ingest documents
- **Hybrid Search**: Combines semantic search with keyword matching for better results

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows 10/11
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: At least 10GB free space

### Required Software

#### 1. Container Runtime (Choose One)

**Option A: Rancher Desktop** (Recommended)
- Download from: https://rancherdesktop.io/
- Supported: macOS, Windows, Linux
- License: Free and open source
- **Important**: Select `dockerd (moby)` as the container runtime in Settings
- Provides: Docker CLI compatibility with `docker-compose` commands

**Option B: Podman**
- Download from: https://podman.io/
- Supported: macOS, Linux, Windows
- License: Free and open source
- Features: Daemonless and can run rootless for better security
- **Note**: Requires `podman-compose` for Compose file support
  - Install: `pip install podman-compose` or `brew install podman-compose` (macOS)

#### 2. Python 3.9 or Higher

- Download from: https://www.python.org/downloads/
- Required for: Langflow and optional document ingestion script
- Recommended: Python 3.10 or 3.11

#### 3. Node.js 18 or Higher

- Download from: https://nodejs.org/
- Required for: Chat UI frontend
- Recommended: Node.js 20 LTS
- Includes: npm (Node Package Manager)

#### 4. API Keys

You'll need at least one of the following:

**Option A: OpenAI API Key**
- Sign up at: https://platform.openai.com/
- Used for: LLM responses and embeddings
- Pricing: Pay-as-you-go

**Option B: IBM watsonx.ai**
- Sign up at: https://www.ibm.com/watsonx
- Used for: LLM responses
- Requires: API key, Project ID, and URL

**Optional: Unstructured.io API Key**
- Only needed if using the Python ingestion script
- Sign up at: https://unstructured.io/
- Used for: Document parsing (PDF, DOCX, etc.)

### Verify Installations

Run these commands to verify your setup:

```bash
# Check container runtime
# For Rancher Desktop:
docker --version
docker-compose --version

# For Podman:
podman --version
podman-compose --version

# Check Python
python --version  # Should be 3.9 or higher
# OR
python3 --version

# Check Node.js and npm
node --version  # Should be 18 or higher
npm --version
```

### Additional Tools (Optional)

- **Git**: For cloning the repository
- **curl**: For testing API endpoints (usually pre-installed on macOS/Linux)
- **Code Editor**: VS Code, Cursor, or your preferred IDE

---

## Installation

### 1. Install OpenSearch

Start OpenSearch using Docker Compose:

**Using Rancher Desktop:**
```bash
docker-compose up -d
```

**Using Podman:**
```bash
podman-compose up -d
# OR
podman compose up -d  # Podman 4.0+
```

> **Note for Rancher Desktop users**: Ensure you have selected `dockerd (moby)` as the container runtime in Rancher Desktop Settings → Container Engine.

Verify it's running:
```bash
curl http://localhost:9200
```

You should see JSON output with OpenSearch version info.

### 2. Install Python & Langflow

Create a virtual environment and install Langflow:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install uv
uv pip install --upgrade langflow
uv pip install fastapi==0.123.6  # Required compatibility fix
```

### 3. Install Frontend Dependencies

Navigate to the frontend directory and install Node.js dependencies:

```bash
cd frontend
npm install
cd ..
```

### 4. (Optional) Install Python Ingestion Script Dependencies

If you plan to use the Python ingestion script:

```bash
pip install -r requirements.txt
```

---

## Configuration

### 1. Set Environment Variables

Choose your LLM provider and set the appropriate API keys:

#### Option 1: IBM watsonx.ai

```bash
export WATSONX_API_KEY="your-api-key"
export WATSONX_PROJECT_ID="your-project-id"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"
```

Recommended models:
- `ibm/granite-13b-chat-v2` for general Q&A
- `meta-llama/llama-3-70b-instruct` for complex reasoning

#### Option 2: OpenAI

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 2. Create OpenSearch Index

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

### 3. Configure Frontend Environment

Create the frontend environment file:

```bash
cd frontend
cp env-example.txt .env.local
```

Edit `.env.local` with your configuration:

```bash
LANGFLOW_URL=http://localhost:7860
LANGFLOW_FLOW_ID=your-flow-id-from-langflow  # You'll get this after importing the flow
LANGFLOW_API_KEY=your-api-key  # Optional: If Langflow authentication is enabled
```

### 4. (Optional) Configure Python Ingestion Script

If using the Python ingestion script, create a `.env` file:

```bash
cp env-example.txt .env
```

Edit `.env` with your API keys:

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

Get API Keys:
- **Unstructured.io**: Sign up at https://unstructured.io/
- **OpenAI**: Get your API key from https://platform.openai.com/

---

## Getting Started

### 1. Start Langflow

```bash
langflow run
```

Open http://localhost:7860 in your browser.

> **Tip**: If you encounter authentication errors, start Langflow with:
> ```bash
> LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true langflow run
> ```

### 2. Import the Pre-built RAG Flow

1. In Langflow, click **My Projects** → **New Project** → **Import**
2. Select `RAG with Opensearch.json` from this repo
3. Update the OpenSearch Vector Store component:
   - **OpenSearch URL**: `http://localhost:9200`
   - **Index Name**: Your index name (default: `hybrid_demo`)
   - **Embedding Model**: Must match your indexed documents
4. Add your API keys (OpenAI or watsonx)
5. Test the flow with a sample query
6. **Copy the Flow ID** from the URL or Settings panel (you'll need this for the frontend)

The flow includes Chat Input, OpenSearch retrieval, RAG prompt, and LLM response components pre-configured.

### 3. Update Frontend Configuration

Add the Flow ID to your frontend `.env.local` file:

```bash
cd frontend
# Edit .env.local and set LANGFLOW_FLOW_ID=your-flow-id-here
```

### 4. Start the Chat UI

```bash
cd frontend
npm run dev
```

Open http://localhost:3000 to start chatting!

---

## Document Ingestion

### Option A: Using Your Existing OpenSearch Index

If you already have documents indexed in OpenSearch, you can easily connect the chat UI to your existing index.

#### Configure Langflow to Use Your Index

1. Open Langflow at http://localhost:7860
2. Open your imported RAG flow (or create a new one)
3. Find the **OpenSearch Vector Store** component in the flow
4. Update the following settings:
   - **Index Name**: Change from `hybrid_demo` to your index name (e.g., `my_documents`)
   - **OpenSearch URL**: Ensure it's set to `http://localhost:9200`
   - **Embedding Model**: Must match the model used during ingestion
5. Save the flow

#### Required Index Schema

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

#### Verify Your Index

Check that your index exists and has documents:

```bash
# List all indices
curl http://localhost:9200/_cat/indices?v

# Check document count
curl http://localhost:9200/YOUR_INDEX_NAME/_count

# View a sample document
curl http://localhost:9200/YOUR_INDEX_NAME/_search?size=1
```

#### Important Notes

- **Embedding Dimensions**: The vector dimension in your index must match the embedding model in Langflow (default: 1536 for OpenAI text-embedding-3-small)
- **Field Names**: Langflow expects `vector_field` for vectors and `text` for content by default
- **Multiple Indices**: You can create multiple Langflow flows, each connected to different indices

### Option B: Python Ingestion Script

If you prefer to use a Python script for document ingestion, we provide a ready-to-use ingestion script.

#### Usage

Run the ingestion script with your documents directory:

```bash
python scripts/ingest_unstructured_opensearch.py --dir ./data
```

**Command Options**:
- `--file`: Ingest a single file
- `--dir`: Ingest all files from a directory
- `--index`: OpenSearch index name (default: `hybrid_demo`)
- `--recreate`: Delete and recreate the index before ingestion
- `--llm-keywords`: Use LLM for keyword extraction (more accurate but costs API calls)

**Supported file types**: PDF, DOCX, TXT, MD, HTML

#### What the Script Does

1. **Document Processing**: Uses Unstructured.io API to extract text from various document formats
2. **Text Chunking**: Splits documents into 1000-character chunks with 200-character overlap
3. **Keyword Extraction**: Extracts keywords for hybrid search (heuristic or LLM-based)
4. **Embedding Generation**: Creates vector embeddings using OpenAI's `text-embedding-3-small` model
5. **Indexing**: Stores chunks with embeddings in OpenSearch with hybrid search configuration

#### Verify Ingestion

```bash
# Check document count
curl http://localhost:9200/hybrid_demo/_count

# View sample documents
curl http://localhost:9200/hybrid_demo/_search?size=3
```

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

**Using Rancher Desktop:**
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

**Using Podman:**
```bash
# Start services
podman-compose up -d

# Check status
podman-compose ps

# View logs
podman-compose logs -f opensearch

# Stop services
podman-compose down

# Stop and remove all data
podman-compose down -v
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

## Troubleshooting

**SSL Error: `[SSL] record layer failure`**

Langflow is trying HTTPS but local OpenSearch uses HTTP. Ensure your URL is `http://localhost:9200` (not `https://`).

**`nmslib engine is deprecated`**

OpenSearch 3.x removed the nmslib engine. Pre-create the index with `faiss` engine as shown in the Configuration section.

**`Field 'vector_field' is not knn_vector type`**

The index was created with the wrong configuration. Delete it and recreate:
```bash
curl -X DELETE "http://localhost:9200/hybrid_demo"
# Then run the create index command from the Configuration section
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

**Port already in use**

```bash
# Check what's using the port
lsof -i :3000  # or :7860, :9200

# Stop the process or change ports in configs
```

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
