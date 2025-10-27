"""Elasticsearch implementation for search functionality."""
from typing import List, Optional
from elasticsearch import AsyncElasticsearch

from domain.entities import Pair
from domain.interfaces import ISearchEngine


class ElasticsearchEngine(ISearchEngine):
    """Elasticsearch implementation of ISearchEngine."""

    def __init__(self, client: AsyncElasticsearch, index_name: str):
        """Initialize with Elasticsearch client."""
        self.client = client
        self.index_name = index_name

    async def index_pair(self, pair: Pair) -> None:
        """Index a pair for searching."""
        document = {
            "field1": pair.field1,
            "field2": pair.field2,
            "created_at": pair.created_at.isoformat() if pair.created_at else None,
            "updated_at": pair.updated_at.isoformat() if pair.updated_at else None
        }

        await self.client.index(
            index=self.index_name,
            id=pair.id,
            document=document
        )

    async def search_pairs(self, query: str) -> List[str]:
        """Search pairs and return list of IDs."""
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["field1", "field2"]
                }
            }
        }

        result = await self.client.search(
            index=self.index_name,
            body=search_query
        )

        return [hit["_id"] for hit in result["hits"]["hits"]]

    async def delete_pair_index(self, pair_id: str) -> None:
        """Remove pair from search index."""
        try:
            await self.client.delete(
                index=self.index_name,
                id=pair_id
            )
        except Exception:
            # Ignore if document doesn't exist
            pass

    async def delete_all_indices(self) -> None:
        """Clear all search indices."""
        try:
            await self.client.delete_by_query(
                index=self.index_name,
                body={"query": {"match_all": {}}}
            )
        except Exception:
            pass


class ElasticsearchConnection:
    """Elasticsearch connection manager."""

    def __init__(self, url: str, index_name: str):
        """Initialize connection parameters."""
        self.url = url
        self.index_name = index_name
        self.client: Optional[AsyncElasticsearch] = None

    async def connect(self):
        """Establish connection to Elasticsearch."""
        self.client = AsyncElasticsearch([self.url])

        # Create index if doesn't exist
        if not await self.client.indices.exists(index=self.index_name):
            await self.client.indices.create(
                index=self.index_name,
                body={
                    "mappings": {
                        "properties": {
                            "field1": {"type": "text"},
                            "field2": {"type": "integer"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"}
                        }
                    }
                }
            )

        print(f"Connected to Elasticsearch: {self.index_name}")

    async def disconnect(self):
        """Close Elasticsearch connection."""
        if self.client:
            await self.client.close()
            print("Disconnected from Elasticsearch")

    def get_client(self) -> AsyncElasticsearch:
        """Get Elasticsearch client."""
        if not self.client:
            raise RuntimeError("Elasticsearch not connected")
        return self.client
