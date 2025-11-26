"""Memory storage implementation using MongoDB and ChromaDB."""

import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
import chromadb
from chromadb.config import Settings as ChromaSettings

from src.memory.nodes import MemoryNode, UserIdentity, MemoryType
from src.utils.config import settings

logger = structlog.get_logger()


class MemoryStorage:
    """Handles storage and retrieval of memories using MongoDB and ChromaDB."""
    
    def __init__(self):
        """Initialize storage connections."""
        # MongoDB connection
        self.mongo_client = MongoClient(settings.mongodb_uri)
        self.db = self.mongo_client[settings.mongodb_database]
        self.memory_collection: Collection = self.db[settings.mongodb_memory_collection]
        self.identity_collection: Collection = self.db[settings.mongodb_user_identity_collection]
        
        # ChromaDB connection for vector search
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info("Memory storage initialized", 
                   mongodb_database=settings.mongodb_database,
                   chroma_collection=settings.chroma_collection_name)
    
    def save_memory(self, memory: MemoryNode) -> str:
        """Save a memory node to both MongoDB and ChromaDB."""
        try:
            # Convert to dict for MongoDB
            memory_dict = memory.model_dump()
            memory_dict["_id"] = memory.memory_id
            
            # Save to MongoDB
            self.memory_collection.replace_one(
                {"_id": memory.memory_id},
                memory_dict,
                upsert=True
            )
            
            # Save embedding to ChromaDB if available
            if memory.embedding:
                self.chroma_collection.upsert(
                    ids=[memory.memory_id],
                    embeddings=[memory.embedding],
                    metadatas=[{
                        "user_id": memory.user_id,
                        "memory_type": memory.memory_type.value,
                        "timestamp": memory.timestamp.isoformat(),
                        "is_hive_mind": str(memory.is_hive_mind),
                        "tags": ",".join(memory.tags) if memory.tags else ""
                    }],
                    documents=[memory.content]
                )
            
            logger.info("Memory saved", memory_id=memory.memory_id, user_id=memory.user_id)
            return memory.memory_id
            
        except Exception as e:
            logger.error("Failed to save memory", error=str(e), memory_id=memory.memory_id)
            raise
    
    def get_user_identity(self, user_id: str) -> Optional[UserIdentity]:
        """Retrieve user identity from MongoDB."""
        try:
            identity_doc = self.identity_collection.find_one({"_id": user_id})
            if identity_doc:
                identity_doc.pop("_id", None)
                return UserIdentity(**identity_doc)
            return None
        except Exception as e:
            logger.error("Failed to get user identity", error=str(e), user_id=user_id)
            return None
    
    def update_user_identity(self, identity: UserIdentity) -> bool:
        """Update or create user identity in MongoDB."""
        try:
            identity_dict = identity.model_dump()
            identity_dict["_id"] = identity.user_id
            identity_dict["updated_at"] = datetime.utcnow()
            
            self.identity_collection.replace_one(
                {"_id": identity.user_id},
                identity_dict,
                upsert=True
            )
            
            logger.info("User identity updated", user_id=identity.user_id)
            return True
        except Exception as e:
            logger.error("Failed to update user identity", error=str(e), user_id=identity.user_id)
            return False
    
    def search_memories(
        self,
        query_embedding: List[float],
        user_id: Optional[str] = None,
        is_hive_mind: bool = False,
        limit: int = 3,
        memory_types: Optional[List[MemoryType]] = None
    ) -> List[MemoryNode]:
        """Search memories using vector similarity."""
        try:
            # Build metadata filter for ChromaDB
            # ChromaDB uses simple key-value pairs or $and/$or for multiple conditions
            where_clause: Optional[Dict[str, Any]] = None
            
            # Start with is_hive_mind condition
            if user_id and not is_hive_mind:
                # For personal memories, filter by both user_id and is_hive_mind
                where_clause = {
                    "$and": [
                        {"is_hive_mind": str(is_hive_mind)},
                        {"user_id": user_id}
                    ]
                }
            else:
                # For hive mind memories, just filter by is_hive_mind
                where_clause = {"is_hive_mind": str(is_hive_mind)}
            
            # Add memory type filter if specified
            if memory_types:
                memory_type_values = [mt.value for mt in memory_types]
                if len(memory_type_values) == 1:
                    # Single memory type - add to existing where clause
                    if "$and" in where_clause:
                        where_clause["$and"].append({"memory_type": memory_type_values[0]})
                    else:
                        where_clause = {
                            "$and": [
                                where_clause,
                                {"memory_type": memory_type_values[0]}
                            ]
                        }
                else:
                    # Multiple memory types - use $or
                    type_conditions = [{"memory_type": mt} for mt in memory_type_values]
                    if "$and" in where_clause:
                        where_clause["$and"].append({"$or": type_conditions})
                    else:
                        where_clause = {
                            "$and": [
                                where_clause,
                                {"$or": type_conditions}
                            ]
                        }
            
            # Query ChromaDB
            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": limit
            }
            
            # Only add where clause if we have one
            if where_clause:
                query_kwargs["where"] = where_clause
            
            results = self.chroma_collection.query(**query_kwargs)
            
            # Retrieve full memory documents from MongoDB
            memory_ids = results["ids"][0] if results["ids"] else []
            if not memory_ids:
                return []
            
            memory_docs = self.memory_collection.find({"_id": {"$in": memory_ids}})
            
            memories = []
            for doc in memory_docs:
                doc.pop("_id", None)
                memories.append(MemoryNode(**doc))
            
            # Sort by recency_value (descending)
            memories.sort(key=lambda m: m.recency_value, reverse=True)
            
            logger.info("Memories retrieved", 
                       count=len(memories),
                       user_id=user_id,
                       is_hive_mind=is_hive_mind)
            return memories
            
        except Exception as e:
            logger.error("Failed to search memories", error=str(e))
            return []
    
    def get_recent_memories(
        self,
        user_id: Optional[str] = None,
        is_hive_mind: bool = False,
        limit: int = 3
    ) -> List[MemoryNode]:
        """Get most recent memories by timestamp."""
        try:
            query: Dict[str, Any] = {"is_hive_mind": is_hive_mind}
            if user_id and not is_hive_mind:
                query["user_id"] = user_id
            
            memory_docs = self.memory_collection.find(query).sort(
                "timestamp", -1
            ).limit(limit)
            
            memories = []
            for doc in memory_docs:
                doc.pop("_id", None)
                memories.append(MemoryNode(**doc))
            
            return memories
        except Exception as e:
            logger.error("Failed to get recent memories", error=str(e))
            return []
    
    def close(self):
        """Close database connections."""
        self.mongo_client.close()
        logger.info("Memory storage connections closed")

