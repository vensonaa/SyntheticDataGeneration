"""
Groq configuration for synthetic data generation
"""

from typing import Dict, Any, Optional
from .env_config import EnvConfig

# Import ChatGroq only when needed to avoid compatibility issues
def get_chat_groq():
    try:
        from langchain_groq import ChatGroq
        return ChatGroq
    except ImportError:
        raise ImportError("langchain-groq is not installed. Run: pip install langchain-groq")


class GroqConfig:
    """Configuration for Groq models and settings"""
    
    # Available Groq models
    MODELS = {
        "llama3-8b-8192": {
            "name": "llama3-8b-8192",
            "description": "Fast and efficient 8B parameter model",
            "max_tokens": 8192,
            "best_for": "General data generation, fast inference"
        },
        "llama3-70b-8192": {
            "name": "llama3-70b-8192", 
            "description": "High-quality 70B parameter model",
            "max_tokens": 8192,
            "best_for": "Complex data generation, high quality"
        },
        "mixtral-8x7b-32768": {
            "name": "mixtral-8x7b-32768",
            "description": "Mixture of experts model with large context",
            "max_tokens": 32768,
            "best_for": "Large context, complex relationships"
        },
        "gemma2-9b-it": {
            "name": "gemma2-9b-it",
            "description": "Google's Gemma 2 model, instruction-tuned",
            "max_tokens": 8192,
            "best_for": "Instruction following, structured data"
        }
    }
    
    # Temperature settings for different use cases
    TEMPERATURE_PRESETS = {
        "creative": 0.8,
        "balanced": 0.5,
        "consistent": 0.3,
        "precise": 0.1
    }
    
    @classmethod
    def create_llm(cls, model_name: str = None, 
                   temperature: float = None,
                   groq_api_key: str = None):
        """
        Create a Groq LLM instance with specified settings
        
        Args:
            model_name: Name of the Groq model to use (uses env default if None)
            temperature: Temperature for generation (0.0 to 1.0) (uses env default if None)
            groq_api_key: Groq API key (uses environment variable if None)
            
        Returns:
            Configured ChatGroq instance
        """
        # Use environment defaults if not specified
        if model_name is None:
            model_name = EnvConfig.get_default_model()
        if temperature is None:
            temperature = EnvConfig.get_default_temperature()
        if groq_api_key is None:
            groq_api_key = EnvConfig.get_groq_api_key()
        
        if model_name not in cls.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Available models: {list(cls.MODELS.keys())}")
        
        if not groq_api_key:
            raise ValueError("Groq API key not found. Please set GROQ_API_KEY in your .env file")
        
        ChatGroq = get_chat_groq()
        return ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model_name,
            temperature=temperature
        )
    
    @classmethod
    def get_model_info(cls, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        return cls.MODELS.get(model_name, {})
    
    @classmethod
    def list_models(cls) -> Dict[str, Dict[str, Any]]:
        """List all available models with their information"""
        return cls.MODELS.copy()
    
    @classmethod
    def recommend_model(cls, use_case: str) -> str:
        """
        Recommend a model based on use case
        
        Args:
            use_case: "speed", "quality", "context", "structured"
            
        Returns:
            Recommended model name
        """
        recommendations = {
            "speed": "llama3-8b-8192",
            "quality": "llama3-70b-8192", 
            "context": "mixtral-8x7b-32768",
            "structured": "gemma2-9b-it"
        }
        return recommendations.get(use_case, "llama3-8b-8192")


class GroqOptimizer:
    """Optimization utilities for Groq usage"""
    
    @staticmethod
    def optimize_prompt_for_groq(prompt: str) -> str:
        """
        Optimize prompt for Groq models
        
        Args:
            prompt: Original prompt
            
        Returns:
            Optimized prompt
        """
        # Add Groq-specific optimizations
        optimized = prompt
        
        # Ensure clear instructions
        if "Requirements:" not in optimized:
            optimized += "\n\nRequirements:\n- Be concise and accurate\n- Follow the specified format exactly"
        
        # Add context length optimization
        if len(optimized) > 4000:
            optimized = "IMPORTANT: Keep responses concise and focused.\n\n" + optimized
        
        return optimized
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Rough token estimation for Groq models
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    @staticmethod
    def chunk_large_inputs(text: str, max_tokens: int = 6000) -> list:
        """
        Split large inputs into chunks for Groq processing
        
        Args:
            text: Input text to chunk
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of text chunks
        """
        estimated_tokens = GroqOptimizer.estimate_tokens(text)
        
        if estimated_tokens <= max_tokens:
            return [text]
        
        # Simple chunking by sentences
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = current_chunk + sentence + ". "
            if GroqOptimizer.estimate_tokens(test_chunk) > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
            else:
                current_chunk = test_chunk
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
