from dataclasses import dataclass
from typing import Dict, Optional
import yaml

@dataclass
class AppConfig:
    default_model: str = "gemini"
    max_tokens: int = 8292
    supported_file_types: tuple = (".md", ".mdx", ".rst", ".rstx", ".py", ".html",".ipynb")
    
    # LLM API configurations
    llm_configs: Dict = None
    
    # Translation settings
    glossary_path: Optional[str] = None
    output_directory: str = "translated_files"
    
    @classmethod
    def load_from_yaml(cls, config_path: str) -> 'AppConfig':
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        return cls(**config_data)
