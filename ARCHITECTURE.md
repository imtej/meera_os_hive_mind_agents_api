# Meera OS Architecture

## System Overview

Meera OS implements a three-agent architecture using LangGraph for orchestration, with persistent memory storage and dynamic prompt generation.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│              (CLI / API / Programmatic)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph Workflow                         │
│              (MeeraWorkflow Orchestrator)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐  ┌──────────────┐
│ Vishnu Agent │ │Brahma Interface││ Shiva Agent  │
│              │ │               │ │              │
│ - Intent     │ │ - Gemini 2.5  │ │ - Extract    │
│ - Identity   │ │   Pro Call    │ │   Memories   │
│ - Memory     │ │ - Response    │ │ - Classify   │
│   Retrieval  │ │   Generation  │ │ - Store      │
│ - Prompt     │ │               │ │ - Embeddings │
│   Building   │ │               │ │              │
└──────┬───────┘ └───────┬───────┘ └──────┬───────┘
       │                 │                 │
       │                 │                 │
       └─────────┬───────┴─────────┬───────┘
                 │                 │
                 ▼                 ▼
       ┌─────────────────┐  ┌──────────────┐
       │ Memory Retriever │ │Memory Storage│
       │                  │ │              │
       │ - Vector Search  │ │ - MongoDB    │
       │ - Embeddings     │ │ - ChromaDB   │
       └──────────────────┘ └──────────────┘
```

#### A condensed, implementation-ready blueprint
![A condensed, implementation-ready blueprint](image.png)



## Data Flow

### 1. User Message → Vishnu Agent

**Input:**
- `user_id`: String identifier
- `user_message`: Raw user text

**Vishnu Processing:**
1. **Intent Detection** (optional)
   - Uses lightweight LLM (Gemini 2.0 Flash)
   - Extracts primary intent from message

2. **Identity Management**
   - Retrieves existing user identity from MongoDB
   - Updates identity based on conversation (heuristic or LLM-based)

3. **Memory Retrieval**
   - **Personal Memories**: Vector search + recency for user-specific context
   - **Hive Mind Memories**: Vector search across all users for shared knowledge
   - Falls back to recent memories if vector search yields few results

4. **Prompt Building**
   - Constructs dynamic system prompt with:
     - Core Meera personality
     - User identity profile
     - Recent personal memories (top 3)
     - Recent hive mind memories (top 3)

**Output:**
- `system_prompt`: Complete dynamic prompt string
- `user_identity`: Updated UserIdentity object
- `personal_memories`: List of MemoryNode objects
- `hive_mind_memories`: List of MemoryNode objects
- `intent`: Detected intent string

### 2. Vishnu → Brahma Interface

**Input:**
- `system_prompt`: From Vishnu
- `user_message`: Original user message
- `conversation_history`: Optional previous messages

**Brahma Processing:**
1. **Message Construction**
   - System message: Full dynamic prompt
   - User messages: Conversation history + current message

2. **LLM Call**
   - Model: Gemini 2.5 Pro
   - Temperature: 0.7 (configurable)
   - Max tokens: 4096 (configurable)

3. **Response Generation**
   - Receives LLM response
   - Formats for user consumption

**Output:**
- `response`: Generated text response
- `full_conversation`: Complete context for Shiva
  - System prompt
  - User message
  - Assistant response
  - Conversation history

### 3. Brahma → Shiva Agent

**Input:**
- `user_id`: User identifier
- `full_conversation`: Complete conversation context
- `user_identity`: Updated identity (optional)

**Shiva Processing:**
1. **Memory Extraction**
   - Uses LLM (Gemini 2.0 Flash) to extract memory signals
   - Identifies 1-3 key memories per conversation
   - Extracts: content, type, tags

2. **Memory Classification**
   - Types: `personal_identity`, `preference`, `factual`, `emotional_state`
   - Validates against allowed types

3. **Memory Node Creation**
   - Generates unique memory ID
   - Creates embedding using Google Generative AI embeddings
   - Sets metadata: tags, recency, source, timestamp

4. **Storage**
   - Saves to MongoDB (structured data)
   - Saves to ChromaDB (vector embeddings)
   - Updates user identity if provided

**Output:**
- `memory_ids`: List of created memory node IDs

## Memory System

### Memory Types

1. **Personal Identity** (`personal_identity`)
   - Core traits, characteristics, self-concept
   - Example: "User identifies as a bridge between form and formless"

2. **Preference** (`preference`)
   - Likes, dislikes, choices, tastes
   - Example: "User prefers classic Bollywood movies"

3. **Factual** (`factual`)
   - Objective information, facts, events
   - Example: "User is CEO of Meera OS, founded in 2024"

4. **Emotional State** (`emotional_state`)
   - Feelings, moods, emotional patterns
   - Example: "User experiences morning anxiety and back pain"

### Storage Architecture

**MongoDB Collections:**
- `memory_nodes`: Full memory documents with all metadata
- `user_identities`: User profile and identity information

**ChromaDB:**
- `memory_embeddings`: Vector embeddings for semantic search
- Metadata: user_id, memory_type, timestamp, tags, is_hive_mind

### Retrieval Strategy

1. **Vector Similarity Search**
   - Query embedding generated from user message
   - Cosine similarity search in ChromaDB
   - Filtered by user_id (personal) or is_hive_mind (shared)

2. **Recency Fallback**
   - If vector search returns < limit, fetch recent memories
   - Sorted by timestamp descending
   - Merged and deduplicated

3. **Hybrid Approach**
   - Combines semantic relevance + temporal relevance
   - Sorted by recency_value (new memories = 1.0)

## Configuration System

### Environment Variables (`.env`)

**Required:**
- `GEMINI_API_KEY`: Google Gemini API key

**Optional:**
- `MONGODB_URI`: MongoDB connection (default: `mongodb://localhost:27017`)
- `MONGODB_DATABASE`: Database name (default: `meera_os`)
- `CHROMA_DB_PATH`: Vector DB path (default: `./chroma_db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### YAML Configuration (`config/settings.yaml`)

**Sections:**
- `meera`: Personality, branding, company info
- `memory`: Retrieval limits, classification types, storage config
- `agents`: Agent-specific settings (intent detection, temperature, etc.)

## Error Handling

### Graceful Degradation

1. **Memory Retrieval Failure**
   - Falls back to recent memories
   - Continues with empty memory list if needed

2. **Intent Detection Failure**
   - Continues without intent
   - Logs error but doesn't fail workflow

3. **Memory Update Failure**
   - Shiva node catches exceptions
   - Returns empty memory_ids list
   - Workflow continues successfully

4. **LLM Call Failure**
   - Propagates error to caller
   - Workflow fails gracefully with error message

## Scalability Considerations

### Current Limitations

1. **Synchronous Processing**: All agents run sequentially
2. **Single Workflow Instance**: One workflow per process
3. **No Caching**: Every request retrieves memories fresh

### Production Enhancements

1. **Async Processing**: Use async/await for I/O operations
2. **Connection Pooling**: MongoDB and ChromaDB connection pools
3. **Caching Layer**: Redis for frequently accessed memories
4. **Rate Limiting**: Protect Gemini API from overuse
5. **Batch Processing**: Process multiple conversations in parallel
6. **Monitoring**: Metrics, tracing, alerting

## Security Considerations

1. **API Keys**: Stored in `.env`, never committed
2. **User Data**: Isolated by user_id in MongoDB
3. **Input Validation**: Pydantic models validate all inputs
4. **Error Messages**: Don't expose internal details to users

## Testing Strategy

### Unit Tests
- Individual agent functions
- Memory storage/retrieval
- Prompt building logic

### Integration Tests
- Full workflow execution
- Database operations
- LLM mocking

### End-to-End Tests
- Complete user conversation flow
- Memory persistence across sessions
- Multi-user scenarios

## Future Enhancements

1. **Imagen Integration**: Image generation in Brahma
2. **Advanced Identity Extraction**: LLM-based identity updates
3. **Memory Pruning**: Automatic cleanup of old/irrelevant memories
4. **Multi-modal Memories**: Support for images, audio
5. **Memory Relationships**: Link related memories
6. **Temporal Memory**: Time-aware memory retrieval
7. **Hive Mind Curation**: Quality control for shared memories

