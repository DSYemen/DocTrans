from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import ChatCohere
from langchain_groq import ChatGroq
from langchain_together import ChatTogether

class LLMFactory:
    @staticmethod
    def create_llm(provider: str, api_key: str, model_name: Optional[str] = None, **kwargs):
        """Create and return an LLM instance based on the provider."""
        if provider == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=api_key,
                temperature=0.3,
                **kwargs
            )
        elif provider == "cohere":
            return ChatCohere(
                model=model_name or "command-r-plus-08-2024",
                cohere_api_key=api_key,
                temperature=0.3,
                **kwargs
            )
        elif provider == "groq":
            return ChatGroq(
                model_name=model_name or "llama-3.3-70b-versatile",
                api_key=api_key,
                temperature=0.3,
                **kwargs
            )
        elif provider == "together":
            return ChatTogether(
                model=model_name or "mistralai/Mixtral-8x7B-Instruct-v0.1",
                together_api_key=api_key,
                temperature=0.3,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def get_available_models() -> Dict[str, list]:
        """Return available models for each provider."""
        return {
            "gemini": ["gemini-1-5-pro"],
            "cohere": ["command-r-plus-08-2024", "command-r-08-2024", "command-r"],
            "groq": ["llama-3.3-70b-versatile", "llama-3.2-70b-versatile"],
            "together": [
                "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "meta-llama/Llama-2-70b-chat-hf"
            ]
        }
