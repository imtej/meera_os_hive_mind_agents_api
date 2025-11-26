"""Shiva Agent: Memory updater."""

import structlog
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.memory.storage import MemoryStorage
from src.memory.nodes import MemoryNode, MemoryType, UserIdentity
from src.utils.config import settings, config_loader

logger = structlog.get_logger()


class ShivaAgent:
    """
    Shiva Agent: Memory updater.
    
    Responsibilities:
    - Extract new memory signals from conversation
    - Classify memories into 4 types
    - Format into memory nodes
    - Save into memory database
    - Generate embeddings and metadata
    """
    
    def __init__(self, memory_storage: MemoryStorage):
        """Initialize Shiva Agent."""
        self.memory_storage = memory_storage
        self.config = config_loader.load()
        agent_config = self.config.get("agents", {}).get("shiva", {})
        
        # LLM for memory extraction and classification
        # Using gemini-2.0-flash-lite instead of gemini-2.0-flash-exp for free tier compatibility
        self.extraction_llm = ChatGoogleGenerativeAI(
            # model="gemini-2.0-flash-lite",
            model="gemini-flash-latest",
            google_api_key=settings.gemini_api_key,
            temperature=0.3
        ) if agent_config.get("extraction_enabled", True) else None
        
        # Embeddings model
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.gemini_api_key
        ) if agent_config.get("embedding_enabled", True) else None
        
        self.memory_types = self.config.get("memory", {}).get("classification", {}).get("types", [])
        
        logger.info("Shiva Agent initialized")
    
    def process(
        self,
        user_id: str,
        full_conversation: Dict[str, Any],
        user_identity: Optional[UserIdentity] = None
    ) -> List[str]:
        """
        Process conversation and update memory nodes.
        
        Args:
            user_id: User identifier
            full_conversation: Complete conversation context from Brahma
            user_identity: Optional user identity for context
        
        Returns:
            List of memory IDs that were created/updated
        """
        logger.info("Shiva processing started", user_id=user_id)
        
        try:
            # Extract memory signals
            memory_signals = self._extract_memory_signals(
                full_conversation,
                user_identity
            )
            
            # Create and save memory nodes
            memory_ids = []
            for signal in memory_signals:
                memory_node = self._create_memory_node(
                    user_id=user_id,
                    signal=signal,
                    conversation=full_conversation
                )
                
                if memory_node:
                    memory_id = self.memory_storage.save_memory(memory_node)
                    memory_ids.append(memory_id)
            
            # Update user identity if provided
            if user_identity:
                self.memory_storage.update_user_identity(user_identity)
            
            logger.info("Shiva processing completed",
                       user_id=user_id,
                       memories_created=len(memory_ids))
            
            return memory_ids
            
        except Exception as e:
            logger.error("Failed to process memory update", error=str(e), user_id=user_id)
            return []
    
    def _extract_memory_signals(
        self,
        conversation: Dict[str, Any],
        user_identity: Optional[UserIdentity]
    ) -> List[Dict[str, Any]]:
        """Extract memory signals from conversation."""
        if not self.extraction_llm:
            # Fallback: create a simple memory from the conversation
            return [{
                "content": f"User: {conversation.get('user_message', '')}\nAssistant: {conversation.get('assistant_response', '')}",
                "memory_type": MemoryType.FACTUAL.value,
                "tags": []
            }]
        
        try:
            user_message = conversation.get("user_message", "")
            assistant_response = conversation.get("assistant_response", "")
            
            prompt = f"""Analyze the following conversation and extract important memory signals that should be remembered for future interactions.

User Message: {user_message}

Assistant Response: {assistant_response}

Extract 1-3 key memory signals. For each signal, provide:
1. A concise summary (1-2 sentences)
2. Memory type: one of {', '.join(self.memory_types)}
3. Relevant tags (comma-separated)

Format as JSON array:
[
  {{
    "content": "memory summary",
    "memory_type": "memory_type",
    "tags": ["tag1", "tag2"]
  }}
]

Only extract memories that are:
- About the user's identity, preferences, or important facts
- Emotionally significant
- Relevant for future conversations
- Not already obvious from the conversation

JSON:"""
            
            response = self.extraction_llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            import json
            # Try to extract JSON from response
            try:
                # Find JSON array in response
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    signals = json.loads(json_str)
                else:
                    signals = []
            except json.JSONDecodeError:
                logger.warning("Failed to parse memory signals JSON", response=response_text[:200])
                signals = []
            
            # Validate and normalize signals
            validated_signals = []
            for signal in signals:
                if isinstance(signal, dict) and "content" in signal:
                    validated_signals.append({
                        "content": signal.get("content", ""),
                        "memory_type": signal.get("memory_type", MemoryType.FACTUAL.value),
                        "tags": signal.get("tags", []) if isinstance(signal.get("tags"), list) else []
                    })
            
            logger.debug("Memory signals extracted", count=len(validated_signals))
            return validated_signals if validated_signals else []
            
        except Exception as e:
            logger.error("Failed to extract memory signals", error=str(e))
            # Fallback
            return [{
                "content": f"Conversation about: {conversation.get('user_message', '')[:100]}",
                "memory_type": MemoryType.FACTUAL.value,
                "tags": []
            }]
    
    def _create_memory_node(
        self,
        user_id: str,
        signal: Dict[str, Any],
        conversation: Dict[str, Any]
    ) -> Optional[MemoryNode]:
        """Create a memory node from a memory signal."""
        try:
            # Generate embedding
            embedding = None
            if self.embeddings:
                try:
                    embedding = self.embeddings.embed_query(signal["content"])
                except Exception as e:
                    logger.warning("Failed to generate embedding", error=str(e))
            
            # Determine memory type
            memory_type_str = signal.get("memory_type", MemoryType.FACTUAL.value)
            try:
                memory_type = MemoryType(memory_type_str)
            except ValueError:
                memory_type = MemoryType.FACTUAL
            
            # Create memory node
            memory_node = MemoryNode(
                memory_id=str(uuid.uuid4()),
                user_id=user_id,
                content=signal["content"],
                memory_type=memory_type,
                timestamp=datetime.utcnow(),
                tags=signal.get("tags", []),
                recency_value=1.0,  # New memories have highest recency
                source="conversation",
                embedding=embedding,
                conversation_context=f"User: {conversation.get('user_message', '')}\nAssistant: {conversation.get('assistant_response', '')}",
                system_prompt_snippet=conversation.get("system_prompt", "")[:500],  # First 500 chars
                is_hive_mind=False  # Personal memory by default
            )
            
            return memory_node
            
        except Exception as e:
            logger.error("Failed to create memory node", error=str(e))
            return None
    
    def create_hive_mind_memory(
        self,
        user_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.FACTUAL,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Create a hive mind (shared) memory.
        
        This can be called to share valuable insights across users.
        """
        try:
            # Generate embedding
            embedding = None
            if self.embeddings:
                embedding = self.embeddings.embed_query(content)
            
            memory_node = MemoryNode(
                memory_id=str(uuid.uuid4()),
                user_id=user_id,  # Original creator
                content=content,
                memory_type=memory_type,
                timestamp=datetime.utcnow(),
                tags=tags or [],
                recency_value=1.0,
                source="hive_mind",
                embedding=embedding,
                is_hive_mind=True
            )
            
            memory_id = self.memory_storage.save_memory(memory_node)
            logger.info("Hive mind memory created", memory_id=memory_id, user_id=user_id)
            return memory_id
            
        except Exception as e:
            logger.error("Failed to create hive mind memory", error=str(e))
            return None

