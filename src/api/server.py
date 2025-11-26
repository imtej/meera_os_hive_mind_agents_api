"""FastAPI server for Meera OS (optional production API)."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import structlog

from src.graph.workflow import MeeraWorkflow

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Meera OS API",
    description="The Hive Mind Protocol - Conscious AI Companion",
    version="1.0.0"
)

# Global workflow instance (in production, use dependency injection)
workflow: Optional[MeeraWorkflow] = None


@app.on_event("startup")
async def startup_event():
    """Initialize workflow on startup."""
    global workflow
    logger.info("Initializing Meera OS workflow")
    workflow = MeeraWorkflow()
    logger.info("Meera OS workflow initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global workflow
    if workflow:
        workflow.close()
        logger.info("Meera OS workflow closed")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    user_id: str
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    user_id: str
    intent: Optional[str] = None
    memory_ids: List[str] = []


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    Processes user message through Vishnu → Brahma → Shiva workflow.
    """
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    try:
        logger.info("Chat request received", user_id=request.user_id, message_preview=request.message[:50])
        
        result = workflow.invoke(
            user_id=request.user_id,
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(
            response=result["response"],
            user_id=result["user_id"],
            intent=result.get("intent"),
            memory_ids=result.get("memory_ids", [])
        )
        
    except Exception as e:
        logger.error("Chat request failed", error=str(e), user_id=request.user_id)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "workflow_initialized": workflow is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

