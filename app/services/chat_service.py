
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat interactions with different models"""
    
    def __init__(self):
        # Initialize default model
        self.default_model = "gpt-4o-mini"
        
    def _get_llm(self, model_name: str):
        """Get LLM instance based on model name"""
        # Map frontend model names to LangChain/OpenAI model names
        model_map = {
            "gpt-4o-mini": "gpt-4o-mini",
            "gpt-4o": "gpt-4o",
            "gemini-2.5-pro": "gpt-4o-mini", # Fallback to OpenAI for now if Gemini key not set, or use compatible endpoint
            "llama4": "gpt-4o-mini", # Placeholder
        }
        
        target_model = model_map.get(model_name, self.default_model)
        
        # We can add more specific logic here later (e.g. ChatGoogleGenerativeAI)
        return ChatOpenAI(
            model=target_model,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )

    async def generate_response(self, query: str, model_name: str, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a response using the selected model and retrieved memories.
        """
        llm = self._get_llm(model_name)
        
        # Format context from memories
        context_str = ""
        for i, mem in enumerate(memories, 1):
            source = mem.get("metadata", {}).get("source", "unknown")
            text = mem.get("text", "")
            context_str += f"[Memory {i}] (Source: {source}):\n{text}\n\n"
            
        if not context_str:
            context_str = "No specific memories found."

        # Create prompt
        prompt = ChatPromptTemplate.from_template("""
        You are an intelligent assistant with access to the following long-term memories:
        
        {context}
        
        User Question: {query}
        
        Instructions:
        1. Answer the question based PRIMARILY on the provided memories.
        2. If the memories contain the answer, cite the source (e.g., "[Source: file.pdf]").
        3. If the answer is not in the memories, you can use your general knowledge but mention that it's not from the provided context.
        4. Be concise and helpful.
        """)
        
        # Remove StrOutputParser to get full message with metadata
        chain = prompt | llm
        
        try:
            response_msg = await chain.ainvoke({
                "context": context_str,
                "query": query
            })
            
            # Extract content
            response_text = response_msg.content
            
            # Extract token usage
            usage_metadata = response_msg.response_metadata.get("token_usage", {})
            usage = {
                "prompt_tokens": usage_metadata.get("prompt_tokens", 0),
                "completion_tokens": usage_metadata.get("completion_tokens", 0),
                "total_tokens": usage_metadata.get("total_tokens", 0)
            }
            
            return {
                "answer": response_text,
                "usage": usage,
                "memories_used": [
                    {
                        "text": m.get("text"),
                        "source": m.get("metadata", {}).get("source")
                    } for m in memories
                ]
            }
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "answer": "I apologize, but I encountered an error while generating the response.",
                "error": str(e)
            }

chat_service = ChatService()
