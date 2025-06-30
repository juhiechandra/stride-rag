# Simple RAG Chatbot

A simple Retrieval Augmented Generation (RAG) chatbot that allows you to upload PDF documents and ask questions about their content using Gemini models.

## Features

- **Document Upload**: Upload PDF documents for indexing
- **Vector Search**: Efficient semantic search using FAISS vector database
- **Simple Q&A**: Ask questions about your uploaded documents
- **Chat History**: Maintains conversation context for follow-up questions
- **Clean Interface**: Simple web interface for easy interaction

## API Endpoints

- `/upload-doc`: Upload and index a PDF document
- `/chat`: Ask questions about uploaded documents
- `/documents`: List all indexed documents
- `/delete-doc`: Remove a document from the index
- `/cleanup-documents`: Remove all documents

## Models Supported

### Gemini Models

- gemini-2.5-flash (default) - Supports both text and images

## Setup

1. Clone the repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:

   ```env
   GEMINI_KEY=your_gemini_api_key
   ```

4. Run the backend:

   ```bash
   uvicorn api.main:app --reload
   ```

5. Run the frontend (in a separate terminal):

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Usage Examples

### Upload a Document

```bash
curl -X POST -F "file=@sample.pdf" http://localhost:8000/upload-doc
```

### Ask a Question

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "model": "gemini-2.5-flash"}' \
  http://localhost:8000/chat
```

## Architecture

The system uses a simple and efficient approach:

- **Document Processing**: Extracts text from PDFs using pdfplumber
- **Image Processing**: Analyzes images from PDFs using Gemini 2.5 Flash vision capabilities
- **Text Embedding**: Uses Gemini embedding model for vector storage
- **Vector Storage**: FAISS for efficient semantic similarity search
- **RAG Chain**: LangChain for orchestrating the retrieval and generation process
- **Frontend**: React-based web interface for easy interaction

## Project Structure

```
├── api/                    # Backend API
│   ├── main.py            # FastAPI main application
│   ├── langchain_utils.py # RAG chain utilities
│   ├── faiss_utils.py     # Vector database utilities
│   ├── db_utils.py        # Database utilities
│   ├── pydantic_models.py # API models
│   └── logger.py          # Logging utilities
├── frontend/              # React frontend
│   └── src/
│       ├── pages/         # React pages
│       └── components/    # React components
└── requirements.txt       # Python dependencies
```

## Testing

Run the test suite to verify functionality:

```bash
python -m pytest tests/
```
