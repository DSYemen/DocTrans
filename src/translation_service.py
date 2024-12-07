from typing import Dict, List, Optional
import os
from pathlib import Path
import frontmatter
import markdown
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import UnstructuredMarkdownLoader, UnstructuredHTMLLoader
from langchain.text_splitter import MarkdownTextSplitter

class TranslationService:
    def __init__(self, llm, glossary: Optional[Dict] = None):
        self.llm = llm
        self.glossary = glossary or {}
        self.setup_translation_chain()
        
    def setup_translation_chain(self):
        template = """You are a professional translator. Translate the following text to Arabic. 
        Keep all links, code blocks, images, and special tags unchanged. Only translate the actual text content.
        If any of these terms appear, use the specific translations provided: {glossary}
        
        Text to translate:
        {text}
        
        Translated text:"""
        
        prompt = PromptTemplate.from_template(template)
        self.translation_chain = (
            {"text": RunnablePassthrough(), "glossary": lambda _: str(self.glossary)}
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def split_text(self, text: str, max_tokens: int = 8292) -> List[str]:
        splitter = MarkdownTextSplitter(chunk_size=max_tokens, chunk_overlap=100)
        return splitter.split_text(text)
    
    def translate_content(self, content: str) -> str:
        chunks = self.split_text(content)
        translated_chunks = []
        
        for chunk in chunks:
            translated_chunk = self.translation_chain.invoke(chunk)
            translated_chunks.append(translated_chunk)
            
        return "\n".join(translated_chunks)
    
    def process_file(self, file_path: str, base_output_dir: str, translation_folder: str) -> str:
        """Process a single file for translation.
        
        Args:
            file_path: Path to the input file
            base_output_dir: Base directory for all translations
            translation_folder: Specific folder name for this translation batch
        """
        file_path = Path(file_path)
        
        # Get the relative path from the input_files directory
        try:
            relative_path = file_path.relative_to(Path("input_files"))
        except ValueError:
            try:
                # Try to get relative path from parent of input_files
                relative_path = file_path.relative_to(Path("input_files").parent)
            except ValueError:
                # If all else fails, use the file name
                relative_path = file_path.name
            
        # Create the output path maintaining the directory structure
        output_path = Path(base_output_dir) / translation_folder / relative_path
        os.makedirs(output_path.parent, exist_ok=True)
        
        # Read and translate content
        content = self._read_file(file_path)
        translated_content = self.translate_content(content)
        
        # Save translated content
        self._write_file(output_path, translated_content, file_path.suffix)
        return str(output_path)
    
    def _read_file(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        
        if suffix in ['.md', '.mdx']:
            post = frontmatter.load(file_path)
            return post.content
        elif suffix in ['.rst', '.rstx']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif suffix == '.html':
            loader = UnstructuredHTMLLoader(str(file_path))
            return loader.load()[0].page_content
        elif suffix == '.py':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def _write_file(self, output_path: Path, content: str, suffix: str):
        if suffix in ['.md', '.mdx']:
            # Preserve frontmatter if exists
            try:
                original = frontmatter.load(output_path.with_suffix(suffix))
                with open(output_path, 'w', encoding='utf-8') as f:
                    if original.metadata:
                        f.write(frontmatter.dumps(frontmatter.Post(content, **original.metadata)))
                    else:
                        f.write(content)
            except:
                # If there's no existing file or no frontmatter, just write the content
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
