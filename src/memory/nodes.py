"""Memory node data structures and models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MemoryType(str, Enum):
    """Types of memories in the system."""
    PERSONAL_IDENTITY = "personal_identity"
    PREFERENCE = "preference"
    FACTUAL = "factual"
    EMOTIONAL_STATE = "emotional_state"


class MemoryNode(BaseModel):
    """Represents a single memory node in the system."""
    
    memory_id: str = Field(..., description="Unique identifier for the memory")
    user_id: str = Field(..., description="User ID this memory belongs to")
    content: str = Field(..., description="The actual memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When memory was created")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    recency_value: float = Field(default=1.0, description="Recency score (0-1)")
    source: str = Field(default="conversation", description="Source of the memory")
    
    # Embedding
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    
    # Context
    conversation_context: Optional[str] = Field(
        default=None, description="Context from which memory was extracted"
    )
    system_prompt_snippet: Optional[str] = Field(
        default=None, description="Relevant system prompt section"
    )
    
    # Hive mind flag
    is_hive_mind: bool = Field(default=False, description="Whether this is a shared hive mind memory")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserIdentity(BaseModel):
    """User identity profile that evolves over time."""
    
    user_id: str = Field(..., description="Unique user identifier")
    
    # Core Profile
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    origin: Optional[str] = None
    current_context: Optional[str] = None
    primary_role: Optional[str] = None
    
    # Personal Identity (Life)
    personal_identity: Dict[str, Any] = Field(default_factory=dict)
    
    # Professional Identity (Work)
    professional_identity: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

