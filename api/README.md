# Stride RAG API

The backend API for the Stride RAG Retrieval Augmented Generation system.

## Overview

This FastAPI-based backend provides the core functionality for the Stride RAG system. It handles:

- Document processing and indexing
- Text and image extraction from documents
- Image-to-text conversion for comprehensive document understanding
- Vector embeddings and storage
- RAG chain orchestration
- Chat history management
- Text-based query processing

## Technology Stack

- **FastAPI**: Web framework for building APIs
- **LangChain**: Framework for LLM applications
- **ChromaDB**: Vector database for embeddings
- **SQLite**: Relational database for metadata and chat history
- **Google Generative AI**: For embeddings and text generation in chat
- **OpenAI**: For image-to-text conversion during document processing
- **PyMuPDF & pdfplumber**: For PDF processing

## Project Structure

```
api/
├── chroma_db/          # ChromaDB vector database storage
├── logs/               # Application logs
├── __init__.py         # Package initialization
├── chroma_utils.py     # ChromaDB and document processing utilities
├── db_utils.py         # Database operations
├── langchain_utils.py  # LangChain integration
├── logger.py           # Logging configuration
├── main.py             # FastAPI application
├── pydantic_models.py  # Data models
└── test_hybrid.py      # Test suite
```

## Module Descriptions

- **main.py**: The entry point for the FastAPI application, defines all API endpoints
- **chroma_utils.py**: Handles document processing, image extraction, and vector storage
- **db_utils.py**: Manages SQLite database operations for document metadata and chat history
- **langchain_utils.py**: Configures and manages LangChain components for RAG
- **logger.py**: Sets up logging and performance monitoring
- **pydantic_models.py**: Defines data models for API requests and responses

## Setup and Installation

1. Make sure you have Python 3.9+ installed
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:

   ```
   GEMINI_API_KEY=your_gemini_api_key
   OPENAI_API_KEY=your_openai_api_key  # Used only for image description during document upload
   ```

4. Run the FastAPI server:

   ```bash
   uvicorn api.main:app --reload
   ```

5. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

### Document Management

- `POST /upload-doc`: Upload and index a PDF document (processes both text and images)
- `GET /documents`: List all indexed documents
- `POST /delete-doc`: Remove a document from the index

### Chat and Query

- `POST /chat`: Text-based RAG queries (can retrieve information from both document text and image descriptions)

## Testing

Run the test suite to verify functionality:

```bash
python -m api.test_hybrid
```

## Logging

The application uses a comprehensive logging system with different log files for different components:

- **app.log**: General application logs
- **api.log**: API endpoint logs
- **db.log**: Database operation logs
- **model.log**: Model interaction logs
- **error.log**: Error logs

## Performance Monitoring

The `PerformanceTimer` class in `logger.py` provides timing information for operations, helping identify bottlenecks in the system.

## Contributing

When contributing to the API, please follow these guidelines:

1. Use type hints for all function parameters and return values
2. Add comprehensive docstrings for all functions and classes
3. Log important operations and errors
4. Use the `PerformanceTimer` for operations that might be slow
5. Add tests for new functionality
