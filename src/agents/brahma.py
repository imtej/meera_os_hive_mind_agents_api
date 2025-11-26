"""Brahma Interface: Gemini 2.5 Pro wrapper."""

import structlog
from typing import Dict, Any, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.utils.config import settings, config_loader

logger = structlog.get_logger()


class BrahmaInterface:
    """
    Brahma Interface: Calls Gemini 2.5 Pro/Imagen with dynamic system prompt.
    
    Responsibilities:
    - Accept Vishnu's dynamic system prompt
    - Send prompt + user message to Gemini 2.5 Pro
    - Receive model output
    - Return response to user
    - Send full conversation to Shiva for memory update
    """
    
    def __init__(self):
        """Initialize Brahma Interface."""
        self.config = config_loader.load()
        agent_config = self.config.get("agents", {}).get("brahma", {})
        
        self.llm = ChatGoogleGenerativeAI(
            model=agent_config.get("model", settings.gemini_model),
            google_api_key=settings.gemini_api_key,
            temperature=agent_config.get("temperature", 0.7),
            max_output_tokens=agent_config.get("max_tokens", 4096)
        )
        
        logger.info("Brahma Interface initialized", model=settings.gemini_model)
    
    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response using Gemini 2.5 Pro.
        
        Args:
            system_prompt: The dynamic system prompt from Vishnu
            user_message: The user's message
            conversation_history: Optional previous messages in the conversation
        
        Returns:
            Dictionary containing:
            - response: The LLM response text
            - full_conversation: Complete conversation context for Shiva
        """
        logger.info("Brahma generating response", message_preview=user_message[:50])
        
        try:
            # Build messages list
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history if provided
            if conversation_history:
                # Ensure conversation_history is a list
                if not isinstance(conversation_history, list):
                    logger.warning("conversation_history is not a list, converting", type=type(conversation_history))
                    conversation_history = []
                
                for msg in conversation_history:
                    # Ensure each message is a dict
                    if not isinstance(msg, dict):
                        logger.warning("Skipping non-dict message in history", type=type(msg))
                        continue
                    
                    role = msg.get("role")
                    content = msg.get("content", "")
                    
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        from langchain_core.messages import AIMessage
                        messages.append(AIMessage(content=content))
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            # Generate response
            response = self.llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Build full conversation for Shiva
            full_conversation = {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "assistant_response": response_text,
                "conversation_history": conversation_history or []
            }
            
            logger.info("Brahma response generated", 
                       response_length=len(response_text),
                       conversation_length=len(full_conversation.get("conversation_history", [])))
            
            return {
                "response": response_text,
                "full_conversation": full_conversation
            }
            
        except Exception as e:
            logger.error("Failed to generate response", error=str(e))
            raise
    
    def generate_image(
        self,
        prompt: str,
        **kwargs
    ) -> Optional[str]:
        """
        Generate image using Imagen (if available).
        
        Note: This is a placeholder for future Imagen integration.
        """
        logger.warning("Image generation not yet implemented")
        return None

