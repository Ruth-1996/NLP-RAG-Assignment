
from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False
)

source_index = "anthropic-bm25-index"
new_index = "anthropic-bm25-thai-index"

# Create a separate BM25 index with Thai character n-grams
settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "filter": {
                "thai_ngram_filter": {
                    "type": "ngram",
                    "min_gram": 2,
                    "max_gram": 3
                }
            },
            "analyzer": {
                "thai_ngram": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "thai_ngram_filter"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "content": {
                "type": "text",
                "analyzer": "thai_ngram"
            },
            "contextualized_content": {
                "type": "text",
                "analyzer": "thai_ngram"
            },
            "doc_id": {"type": "keyword"},
            "chunk_id": {"type": "keyword"},
            "original_index": {"type": "integer", "index": False}
        }
    }
}

if not client.indices.exists(index=source_index):
    raise RuntimeError("Original BM25 index not found")

if not client.indices.exists(index=new_index):
    client.indices.create(index=new_index, body=settings)
    print("Created Thai N-gram index")

# Copy existing documents without regenerating embeddings
result = client.reindex(
    body={
        "source": {"index": source_index},
        "dest": {"index": new_index}
    },
    refresh=True,
    request_timeout=180
)

print("Reindexed:", result["total"])
print("Failures:", result["failures"])
print("Document count:", client.count(index=new_index)["count"])
