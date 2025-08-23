"""
Environment configuration for synthetic data generation
"""

import os
from typing import Optional
from dotenv import load_dotenv


class EnvConfig:
    """Environment configuration manager"""
    
    _loaded = False
    
    @classmethod
    def load_env(cls, env_path: str = ".env") -> None:
        """Load environment variables from .env file"""
        if not cls._loaded:
            load_dotenv(env_path)
            cls._loaded = True
    
    @classmethod
    def get_groq_api_key(cls) -> Optional[str]:
        """Get Groq API key from environment"""
        cls.load_env()
        return os.getenv("GROQ_API_KEY")
    
    @classmethod
    def get_default_model(cls) -> str:
        """Get default Groq model"""
        cls.load_env()
        return os.getenv("DEFAULT_GROQ_MODEL", "llama3-8b-8192")
    
    @classmethod
    def get_default_temperature(cls) -> float:
        """Get default temperature setting"""
        cls.load_env()
        return float(os.getenv("DEFAULT_TEMPERATURE", "0.5"))
    
    @classmethod
    def get_default_record_count(cls) -> int:
        """Get default record count"""
        cls.load_env()
        return int(os.getenv("DEFAULT_RECORD_COUNT", "1000"))
    
    @classmethod
    def get_default_batch_size(cls) -> int:
        """Get default batch size"""
        cls.load_env()
        return int(os.getenv("DEFAULT_BATCH_SIZE", "10"))
    
    @classmethod
    def get_recursion_limit(cls) -> int:
        """Get recursion limit for LangGraph"""
        cls.load_env()
        return int(os.getenv("RECURSION_LIMIT", "200"))
    
    @classmethod
    def get_max_retries(cls) -> int:
        """Get maximum retry attempts"""
        cls.load_env()
        return int(os.getenv("MAX_RETRIES", "3"))
    
    @classmethod
    def is_quality_enhancement_enabled(cls) -> bool:
        """Check if quality enhancement is enabled"""
        cls.load_env()
        return os.getenv("ENABLE_QUALITY_ENHANCEMENT", "true").lower() == "true"
    
    @classmethod
    def is_contextual_generation_enabled(cls) -> bool:
        """Check if contextual generation is enabled"""
        cls.load_env()
        return os.getenv("ENABLE_CONTEXTUAL_GENERATION", "true").lower() == "true"
    
    @classmethod
    def get_default_output_format(cls) -> str:
        """Get default output format"""
        cls.load_env()
        return os.getenv("DEFAULT_OUTPUT_FORMAT", "json")
    
    @classmethod
    def is_csv_export_enabled(cls) -> bool:
        """Check if CSV export is enabled"""
        cls.load_env()
        return os.getenv("ENABLE_CSV_EXPORT", "true").lower() == "true"
    
    @classmethod
    def validate_config(cls) -> dict:
        """Validate configuration and return status"""
        cls.load_env()
        
        status = {
            "groq_api_key": bool(cls.get_groq_api_key()),
            "default_model": cls.get_default_model(),
            "default_temperature": cls.get_default_temperature(),
            "default_record_count": cls.get_default_record_count(),
            "quality_enhancement": cls.is_quality_enhancement_enabled(),
            "contextual_generation": cls.is_contextual_generation_enabled(),
            "recursion_limit": cls.get_recursion_limit(),
            "max_retries": cls.get_max_retries()
        }
        
        return status
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration"""
        config = cls.validate_config()
        
        print("🔧 Environment Configuration:")
        print("=" * 40)
        print(f"Groq API Key: {'✅ Set' if config['groq_api_key'] else '❌ Not set'}")
        print(f"Default Model: {config['default_model']}")
        print(f"Default Temperature: {config['default_temperature']}")
        print(f"Default Record Count: {config['default_record_count']}")
        print(f"Quality Enhancement: {'✅ Enabled' if config['quality_enhancement'] else '❌ Disabled'}")
        print(f"Contextual Generation: {'✅ Enabled' if config['contextual_generation'] else '❌ Disabled'}")
        print(f"Recursion Limit: {config['recursion_limit']}")
        print(f"Max Retries: {config['max_retries']}")
        
        if not config['groq_api_key']:
            print("\n⚠️  Warning: GROQ_API_KEY not set in .env file")
            print("   Please add your Groq API key to the .env file:")
            print("   GROQ_API_KEY=your_actual_api_key_here")


def setup_environment(env_path: str = ".env") -> None:
    """Setup environment configuration"""
    EnvConfig.load_env(env_path)
    
    # Validate configuration
    config = EnvConfig.validate_config()
    
    if not config['groq_api_key']:
        print("⚠️  Warning: GROQ_API_KEY not found in environment")
        print("   Some GenAI features may not work without a valid API key")
        print("   Get your API key from: https://console.groq.com")
    
    return config
