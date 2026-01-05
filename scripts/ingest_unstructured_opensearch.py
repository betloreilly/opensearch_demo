#!/usr/bin/env python3
"""
Ingest documents to OpenSearch using Unstructured.io API
Creates proper schema for hybrid search (BM25 + Vector)

Based on: https://docs.unstructured.io/open-source/ingestion/source-connectors/opensearch
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Optional

import httpx
from opensearchpy import OpenSearch, helpers

# ===========================================
# CONFIGURATION - Update these values
# ===========================================

# Unstructured.io API
UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY", "YOUR_UNSTRUCTURED_API_KEY")
UNSTRUCTURED_API_URL = os.getenv("UNSTRUCTURED_API_URL", "https://api.unstructuredapp.io/general/v0/general")

# OpenAI for embeddings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# OpenSearch
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 9200))
INDEX_NAME = os.getenv("INDEX_NAME", "hybrid_demo")

# ===========================================
# OpenSearch Index Schema for Hybrid Search
# ===========================================

INDEX_SCHEMA = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100
        },
        "analysis": {
            "analyzer": {
                # Custom analyzer for better BM25 ranking
                "hybrid_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "english_stemmer",
                        "english_stop",
                        "word_delimiter_graph"
                    ]
                },
                # Analyzer for keywords (no stemming)
                "keyword_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"]
                }
            },
            "filter": {
                "english_stemmer": {
                    "type": "stemmer",
                    "language": "english"
                },
                "english_stop": {
                    "type": "stop",
                    "stopwords": "_english_"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # Unique identifiers
            "record_id": {"type": "keyword"},
            "element_id": {"type": "keyword"},
            
            # Main text field with custom analyzer for BM25 ranking
            "text": {
                "type": "text",
                "analyzer": "hybrid_analyzer",
                "search_analyzer": "hybrid_analyzer",
                "fields": {
                    # Raw subfield for exact matching
                    "raw": {
                        "type": "text",
                        "analyzer": "keyword_analyzer"
                    },
                    # Keyword subfield for aggregations
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            
            # Vector field for semantic search
            "vector_field": {
                "type": "knn_vector",
                "dimension": EMBEDDING_DIMENSION,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "faiss",
                    "parameters": {
                        "ef_construction": 256,
                        "m": 32
                    }
                }
            },
            
            # Metadata fields for filtering
            "metadata": {
                "type": "object",
                "properties": {
                    "filename": {"type": "keyword"},
                    "filetype": {"type": "keyword"},
                    "page_number": {"type": "integer"},
                    "category": {"type": "keyword"},
                    "languages": {"type": "keyword"},
                    "parent_id": {"type": "keyword"},
                    "is_continuation": {"type": "boolean"}
                }
            },
            
            # Title with higher boost for ranking
            "title": {
                "type": "text",
                "analyzer": "hybrid_analyzer",
                "boost": 3.0
            },
            
            # Keywords for exact term matching (important for hybrid)
            "keywords": {
                "type": "text",
                "analyzer": "keyword_analyzer",
                "boost": 2.0,
                "fields": {
                    "exact": {"type": "keyword"}
                }
            },
            
            # Section type for filtering/boosting
            "section": {"type": "keyword"},
            
            # Content summary for better ranking context
            "summary": {
                "type": "text",
                "analyzer": "hybrid_analyzer"
            }
        }
    }
}


# Search pipeline for hybrid score normalization
SEARCH_PIPELINE = {
    "description": "Hybrid search pipeline with score normalization",
    "phase_results_processors": [
        {
            "normalization-processor": {
                "normalization": {
                    "technique": "min_max"
                },
                "combination": {
                    "technique": "arithmetic_mean",
                    "parameters": {
                        "weights": [0.4, 0.6]  # 40% BM25, 60% vector
                    }
                }
            }
        }
    ]
}


def create_opensearch_client() -> OpenSearch:
    """Create OpenSearch client."""
    return OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
    )


def create_search_pipeline(client: OpenSearch, pipeline_name: str = "hybrid_search_pipeline"):
    """Create search pipeline for hybrid score normalization."""
    try:
        # Check if pipeline exists
        client.transport.perform_request('GET', f'/_search/pipeline/{pipeline_name}')
        print(f"[OK] Search pipeline '{pipeline_name}' already exists")
    except Exception:
        # Create the pipeline
        try:
            client.transport.perform_request(
                'PUT', 
                f'/_search/pipeline/{pipeline_name}',
                body=SEARCH_PIPELINE
            )
            print(f"[OK] Created search pipeline '{pipeline_name}' for hybrid score normalization")
        except Exception as e:
            print(f"[WARN] Could not create search pipeline: {e}")
            print("   (Hybrid search will still work, but without score normalization)")


def create_index(client: OpenSearch, index_name: str, recreate: bool = False):
    """Create OpenSearch index with hybrid search schema."""
    if client.indices.exists(index=index_name):
        if recreate:
            print(f"[INFO] Deleting existing index '{index_name}'...")
            client.indices.delete(index=index_name)
        else:
            print(f"[OK] Index '{index_name}' already exists")
            return
    
    client.indices.create(index=index_name, body=INDEX_SCHEMA)
    print(f"[OK] Created index '{index_name}' with hybrid search schema")
    
    # Create search pipeline for hybrid search
    create_search_pipeline(client)


def parse_with_unstructured(file_path: str) -> list[dict]:
    """Parse document using Unstructured.io API."""
    print(f"[INFO] Parsing with Unstructured.io: {Path(file_path).name}")
    
    with open(file_path, "rb") as f:
        files = {"files": (Path(file_path).name, f)}
        
        response = httpx.post(
            UNSTRUCTURED_API_URL,
            headers={"unstructured-api-key": UNSTRUCTURED_API_KEY},
            files=files,
            data={
                "strategy": "hi_res",
                "chunking_strategy": "by_title",
                "max_characters": 1000,
                "overlap": 200,
            },
            timeout=300.0
        )
    
    if response.status_code != 200:
        raise Exception(f"Unstructured API error: {response.status_code} - {response.text}")
    
    elements = response.json()
    print(f"   → Got {len(elements)} elements")
    return elements


def get_embedding(text: str) -> list[float]:
    """Get embedding from OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")
    
    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={"model": EMBEDDING_MODEL, "input": text},
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def clean_metadata(metadata: dict) -> dict:
    """Clean metadata - remove NaN and problematic values."""
    clean = {}
    allowed_keys = ["filename", "filetype", "page_number", "category", "languages", "parent_id", "is_continuation"]
    
    for key in allowed_keys:
        if key in metadata:
            value = metadata[key]
            # Skip NaN, None, and empty values
            if value is None:
                continue
            if isinstance(value, float) and str(value).lower() == 'nan':
                continue
            if isinstance(value, str) and value.strip() == '':
                continue
            clean[key] = value
    
    return clean


def extract_keywords(text: str, use_llm: bool = False) -> list[str]:
    """Extract keywords from text dynamically for hybrid search boost.
    
    Two modes:
    - Heuristic: Fast, free - extracts capitalized terms, numbers, technical patterns
    - LLM: More accurate but costs API calls
    """
    if use_llm and OPENAI_API_KEY:
        return extract_keywords_llm(text)
    return extract_keywords_heuristic(text)


def extract_keywords_heuristic(text: str) -> list[str]:
    """Extract keywords using heuristics - no API calls needed."""
    import re
    
    keywords = set()
    
    # 1. Find capitalized words/acronyms (likely proper nouns or technical terms)
    # Match: BLEU, GPT, Transformer, OpenSearch, etc.
    caps_pattern = r'\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\b'
    for match in re.findall(caps_pattern, text):
        if len(match) >= 2 and match.lower() not in {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'this', 'that', 'these', 'those', 'we', 'our', 'they', 'their', 'it', 'its', 'he', 'she', 'his', 'her', 'i', 'you', 'your', 'my', 'me', 'us', 'them', 'who', 'what', 'which', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'but', 'if', 'because', 'as', 'until', 'while', 'although', 'though', 'after', 'before', 'since', 'unless', 'however', 'therefore', 'thus', 'hence', 'also', 'still', 'yet', 'even', 'here', 'there', 'then', 'now', 'abstract', 'introduction', 'conclusion', 'references', 'figure', 'table'}:
            keywords.add(match.lower())
    
    # 2. Find acronyms (2-5 uppercase letters)
    acronyms = re.findall(r'\b[A-Z]{2,5}\b', text)
    for acr in acronyms:
        if acr.lower() not in {'ii', 'iii', 'iv', 'vi', 'vii', 'viii', 'ix', 'xi', 'xii'}:
            keywords.add(acr)
    
    # 3. Find numbers with context (e.g., "28.4 BLEU", "41.8%", "3.5 days")
    num_pattern = r'(\d+\.?\d*)\s*(%|BLEU|days?|hours?|layers?|heads?|dimensions?|parameters?)'
    for match in re.findall(num_pattern, text, re.IGNORECASE):
        keywords.add(f"{match[0]} {match[1]}".strip())
    
    # 4. Find hyphenated terms (often technical: multi-head, self-attention)
    hyphen_terms = re.findall(r'\b[a-zA-Z]+-[a-zA-Z]+(?:-[a-zA-Z]+)*\b', text)
    for term in hyphen_terms:
        if len(term) >= 5:
            keywords.add(term.lower())
    
    # 5. Find camelCase or special patterns
    camel_case = re.findall(r'\b[a-z]+[A-Z][a-zA-Z]*\b', text)
    for term in camel_case:
        keywords.add(term)
    
    # Return top keywords (limit to 15)
    return list(keywords)[:15]


def extract_keywords_llm(text: str) -> list[str]:
    """Extract keywords using OpenAI LLM - more accurate but costs API calls."""
    try:
        # Truncate text to save tokens
        truncated = text[:1000] if len(text) > 1000 else text
        
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "Extract 5-10 important keywords/key phrases from the text. Return ONLY a comma-separated list, no explanation."
                    },
                    {
                        "role": "user", 
                        "content": truncated
                    }
                ],
                "max_tokens": 100,
                "temperature": 0
            },
            timeout=15.0
        )
        response.raise_for_status()
        
        keywords_str = response.json()["choices"][0]["message"]["content"]
        keywords = [k.strip().lower() for k in keywords_str.split(",")]
        return keywords[:10]
    except Exception as e:
        print(f"   [WARN] LLM keyword extraction failed: {e}, falling back to heuristic")
        return extract_keywords_heuristic(text)


# Global flag for LLM keyword extraction
USE_LLM_KEYWORDS = False


def prepare_documents(elements: list[dict], filename: str) -> list[dict]:
    """Prepare documents for OpenSearch indexing."""
    documents = []
    
    for i, element in enumerate(elements):
        text = element.get("text", "")
        if not text or len(text.strip()) < 10:
            continue
        
        # Generate unique ID
        record_id = hashlib.md5(f"{filename}_{i}_{text[:50]}".encode()).hexdigest()
        
        # Get embedding
        print(f"   Embedding chunk {i+1}/{len(elements)}...", end='\r')
        try:
            embedding = get_embedding(text)
        except Exception as e:
            print(f"\n   [WARN] Embedding failed for chunk {i+1}: {e}")
            continue
        
        # Clean metadata
        raw_metadata = element.get("metadata", {})
        metadata = clean_metadata(raw_metadata)
        metadata["filename"] = filename
        
        # Extract keywords for hybrid search (dynamic extraction)
        keywords_list = extract_keywords(text, use_llm=USE_LLM_KEYWORDS)
        # Join keywords as text for BM25 matching
        keywords_text = " ".join(keywords_list) if keywords_list else ""
        
        # Create summary (first sentence or first 200 chars)
        summary = text[:200].rsplit(' ', 1)[0] + "..." if len(text) > 200 else text
        
        # Detect section/title from element type
        element_type = element.get("type", "")
        section = None
        title = None
        if element_type == "Title":
            title = text
            section = "title"
        elif element_type == "Header":
            title = text  # Headers can also be titles
            section = "header"
        elif element_type == "ListItem":
            section = "list"
        elif element_type == "Table":
            section = "table"
        elif element_type == "NarrativeText":
            section = "narrative"
        else:
            section = "content"
        
        doc = {
            "_index": INDEX_NAME,
            "_id": record_id,
            "_source": {
                "record_id": record_id,
                "element_id": element.get("element_id", ""),
                "text": text,
                "vector_field": embedding,
                "metadata": metadata,
                "keywords": keywords_text,  # Text field for BM25 matching
                "section": section,
                "title": title,
                "summary": summary,
            }
        }
        documents.append(doc)
    
    print(f"\n   [OK] Prepared {len(documents)} documents with embeddings")
    return documents


def ingest_file(client: OpenSearch, file_path: str):
    """Ingest a single file into OpenSearch."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return 0
    
    # Parse with Unstructured.io
    elements = parse_with_unstructured(file_path)
    
    if not elements:
        print(f"   [WARN] No elements extracted from {path.name}")
        return 0
    
    # Prepare documents with embeddings
    documents = prepare_documents(elements, path.name)
    
    if not documents:
        print(f"   [WARN] No valid documents to index")
        return 0
    
    # Index documents one by one for better error visibility
    print(f"   [INFO] Indexing {len(documents)} documents...")
    success_count = 0
    error_count = 0
    
    for doc in documents:
        try:
            client.index(
                index=doc["_index"],
                id=doc["_id"],
                body=doc["_source"]
            )
            success_count += 1
        except Exception as e:
            error_count += 1
            if error_count <= 3:
                print(f"   [WARN] Index error: {e}")
    
    # Force refresh to make documents searchable immediately
    try:
        client.indices.refresh(index=INDEX_NAME)
    except Exception:
        pass
    
    print(f"   [OK] Indexed {success_count} documents ({error_count} errors)")
    return success_count


def ingest_directory(client: OpenSearch, dir_path: str):
    """Ingest all supported files from a directory."""
    path = Path(dir_path)
    supported_extensions = {".pdf", ".docx", ".doc", ".txt", ".md", ".html"}
    
    files = [f for f in path.iterdir() if f.suffix.lower() in supported_extensions]
    
    if not files:
        print(f"[ERROR] No supported files found in {dir_path}")
        return
    
    print(f"[INFO] Found {len(files)} files to process")
    
    total_indexed = 0
    for file_path in files:
        try:
            indexed = ingest_file(client, str(file_path))
            total_indexed += indexed
        except Exception as e:
            print(f"[ERROR] Error processing {file_path.name}: {e}")
    
    print(f"\n{'='*50}")
    print(f"[OK] Total indexed: {total_indexed} documents")


def main():
    global INDEX_NAME, USE_LLM_KEYWORDS
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest documents to OpenSearch with Unstructured.io")
    parser.add_argument("--file", type=str, help="Single file to ingest")
    parser.add_argument("--dir", type=str, help="Directory to ingest")
    parser.add_argument("--index", type=str, default="hybrid_demo", help="Index name")
    parser.add_argument("--recreate", action="store_true", help="Recreate index")
    parser.add_argument("--llm-keywords", action="store_true", help="Use LLM for keyword extraction (costs API calls)")
    
    args = parser.parse_args()
    
    # Validate API keys
    if UNSTRUCTURED_API_KEY == "YOUR_UNSTRUCTURED_API_KEY":
        print("[ERROR] Please set UNSTRUCTURED_API_KEY environment variable")
        print("   export UNSTRUCTURED_API_KEY='your-key-here'")
        return
    
    if not OPENAI_API_KEY:
        print("[ERROR] Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-key-here'")
        return
    
    INDEX_NAME = args.index
    USE_LLM_KEYWORDS = args.llm_keywords
    
    print("="*50)
    print("OpenSearch Hybrid Search Ingestion")
    print("="*50)
    print(f"Index: {INDEX_NAME}")
    print(f"Unstructured API: {UNSTRUCTURED_API_URL}")
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    print(f"Keyword Extraction: {'LLM (OpenAI)' if USE_LLM_KEYWORDS else 'Heuristic (fast/free)'}")
    print()
    
    # Connect to OpenSearch
    client = create_opensearch_client()
    
    try:
        info = client.info()
        print(f"[OK] Connected to OpenSearch {info['version']['number']}")
    except Exception as e:
        print(f"[ERROR] Failed to connect to OpenSearch: {e}")
        return
    
    # Create index
    create_index(client, INDEX_NAME, recreate=args.recreate)
    
    # Ingest
    if args.file:
        ingest_file(client, args.file)
    elif args.dir:
        ingest_directory(client, args.dir)
    else:
        # Default: ingest demo docs
        demo_dir = Path(__file__).parent.parent / "data" / "demo_docs"
        if demo_dir.exists():
            ingest_directory(client, str(demo_dir))
        else:
            print("[ERROR] No input specified. Use --file or --dir")
            print(f"   Or create demo docs: python scripts/download_demo_pdfs.py")
    
    # Show final count
    try:
        count = client.count(index=INDEX_NAME)["count"]
    except Exception:
        count = "unknown"
    print(f"\n[DONE] Total documents in '{INDEX_NAME}': {count}")


if __name__ == "__main__":
    main()

