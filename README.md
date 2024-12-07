# AI Documentation Translator

An advanced Streamlit application that translates documentation files from GitHub repositories using various Large Language Models (LLMs). The application supports multiple file formats and maintains the original formatting while translating content to Arabic.

## Features

- 📚 Multi-format Support:
  - Markdown (.md)
  - MDX (.mdx)
  - ReStructuredText (.rst, .rstx)
  - Python (.py)
  - HTML (.html)
- 🤖 Multiple LLM Providers:
  - Google Gemini
  - Cohere
  - Groq
  - Together AI
- 🔄 Smart Features:
  - Automatic token splitting for large files
  - Custom glossary support
  - Preserves formatting, code blocks, and special elements
  - Maintains directory structure
- 🌐 GitHub Integration:
  - Repository-specific downloads
  - Branch selection
  - Folder/file filtering
  - Automatic folder naming

## Directory Structure

```
.
├── input_files/               # Base directory for downloaded files
│   └── [repository_name]/     # Repository-specific downloads
├── output_files/             # Base directory for translated files
│   └── [repository_name]/    # Repository-specific translations
├── src/                      # Source code
│   ├── app.py               # Main Streamlit application
│   ├── config.py            # Configuration management
│   ├── github_service.py    # GitHub integration
│   ├── llm_factory.py       # LLM provider management
│   └── translation_service.py  # Translation logic
├── config.yaml              # Application configuration
├── requirements.txt         # Project dependencies
└── README.md               # Documentation
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-doc-translator.git
cd ai-doc-translator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key
COHERE_API_KEY=your_cohere_api_key
GROQ_API_KEY=your_groq_api_key
TOGETHER_API_KEY=your_together_api_key
GITHUB_TOKEN=your_github_token  # Optional
```

## Usage

1. Run the Streamlit application:
```bash
streamlit run src/app.py
```

2. Enter GitHub repository information:
   - Repository URL
   - Branch name (defaults to "main")
   - Folder path (e.g., "docs/folder/")
   - Optional specific file path

3. The application will automatically:
   - Create input folder using repository name
   - Create output folder using repository name
   - Maintain the original directory structure

4. Select files to translate and click "Start Translation"

## Custom Glossary

Create a YAML file with your custom translations:

```yaml
terms:
  "machine learning": "التعلم الآلي"
  "deep learning": "التعلم العميق"
  "artificial intelligence": "الذكاء الاصطناعي"
```

## File Organization

- Downloaded files are stored in: `input_files/[repository_name]/`
- Translated files are stored in: `output_files/[repository_name]/`
- Original directory structure is maintained in both locations

## Translation Process

1. Files are downloaded to the input directory
2. Large files are automatically split into manageable chunks
3. Only text content is translated; code, links, and formatting are preserved
4. Translated content is saved with the same structure in the output directory
5. Input files are automatically cleaned up after successful translation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
