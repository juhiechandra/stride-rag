# Multimodal RAG System

A Retrieval Augmented Generation (RAG) system that supports both text and image processing using Gemini and OpenAI models.

## Features

- **Document Processing**: Upload and index PDF documents with both text and image content
- **Text RAG**: Standard text-based retrieval augmented generation
- **Image Processing**: Extract and analyze images from documents
- **Multimodal Queries**: Ask questions about text and images
- **Multiple Models**: Support for both Google Gemini and OpenAI models
- **Chat History**: Maintains conversation context for follow-up questions

## API Endpoints

- `/upload-doc`: Upload and index a PDF document
- `/chat`: Text-based RAG queries
- `/multimodal-chat`: Process queries with optional image input
- `/documents`: List all indexed documents
- `/delete-doc`: Remove a document from the index

## Models Supported

### Gemini Models

- gemini-2.0-flash
- gemini-2.0-flash

### OpenAI Models

- gpt-4o-mini
- gpt-4o

## Setup

1. Clone the repository
2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:

   ```
   GEMINI_API_KEY=your_gemini_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

4. Run the application:

   ```
   uvicorn api.main:app --reload
   ```

## Usage Examples

### Upload a Document

```bash
curl -X POST -F "file=@sample.pdf" http://localhost:8000/upload-doc
```

### Text Query

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?", "model": "gemini-2.0-flash"}' \
  http://localhost:8000/chat
```

### Multimodal Query with Image

```bash
curl -X POST \
  -F "question=What's in this image?" \
  -F "model=gpt-4o-mini" \
  -F "image=@sample_image.jpg" \
  http://localhost:8000/multimodal-chat
```

## Architecture

The system uses a hybrid approach:

- **Document Indexing**: Extracts text with pdfplumber and images with PyMuPDF
- **Text Embedding**: Uses Gemini embedding model for vector storage
- **Image Analysis**: Uses OpenAI vision capabilities to generate descriptions
- **Vector Storage**: ChromaDB for efficient similarity search
- **RAG Chain**: LangChain for orchestrating the retrieval and generation process

## Testing

Run the test suite to verify functionality:

```bash
python -m api.test_hybrid
```
