# Stride RAG - Multimodal Retrieval Augmented Generation System

A powerful Retrieval Augmented Generation (RAG) system that supports both text and image processing using Google Gemini and OpenAI models.

## 📋 Overview

Stride RAG is a comprehensive solution for document processing and intelligent querying that combines the power of large language models with efficient retrieval mechanisms. The system can process both text and images from documents, enabling multimodal interactions.

## ✨ Features

- **Document Processing**: Upload and index PDF documents with both text and image content
- **Text RAG**: Standard text-based retrieval augmented generation using Gemini models
- **Image Processing**: Extract and analyze images from documents using OpenAI GPT-4o-mini
- **Multimodal Queries**: Ask questions about text and images
- **Model Specialization**: Gemini models for RAG operations, OpenAI only for image descriptions
- **Token Usage Tracking**: Comprehensive logging of token usage for all model interactions
- **Chat History**: Maintains conversation context for follow-up questions
- **Performance Monitoring**: Built-in logging and performance tracking

## 🏗️ Architecture

The system uses a hybrid approach:

- **Backend**: FastAPI-based REST API
- **Frontend**: React-based web interface
- **Document Indexing**: Extracts text with pdfplumber and images with PyMuPDF
- **Text Embedding**: Uses Gemini embedding model for vector storage
- **Image Analysis**: Uses OpenAI GPT-4o-mini vision capabilities to generate descriptions
- **Vector Storage**: ChromaDB for efficient similarity search
- **RAG Chain**: LangChain for orchestrating the retrieval and generation process
- **Database**: SQLite for storing document metadata and chat history
- **Logging**: Comprehensive logging system with separate logs for application, API, database, errors, and token usage

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- API keys for Google Gemini and OpenAI

### Backend Setup

1. Clone the repository

   ```bash
   git clone https://github.com/yourusername/stride-rag.git
   cd stride-rag
   ```

2. Install Python dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`

   ```
   GEMINI_API_KEY=your_gemini_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

4. Run the FastAPI server

   ```bash
   uvicorn api.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory

   ```bash
   cd frontend
   ```

2. Install Node.js dependencies

   ```bash
   npm install
   ```

3. Start the development server

   ```bash
   npm run dev
   ```

4. Access the application at `http://localhost:5173`

## 📁 Project Structure

```
stride-rag/
├── api/                    # Backend API code
│   ├── chroma_db/          # ChromaDB vector database storage
│   ├── logs/               # Application logs
│   │   ├── app.log         # General application logs
│   │   ├── api.log         # API request logs
│   │   ├── db.log          # Database operation logs
│   │   ├── error.log       # Error logs
│   │   ├── model.log       # Model interaction logs
│   │   └── token_usage.log # Token usage tracking
│   ├── chroma_utils.py     # ChromaDB and document processing utilities
│   ├── db_utils.py         # Database operations
│   ├── langchain_utils.py  # LangChain integration
│   ├── logger.py           # Logging configuration
│   ├── main.py             # FastAPI application
│   └── pydantic_models.py  # Data models
├── frontend/               # React frontend
│   ├── public/             # Static assets
│   ├── src/                # Source code
│   │   ├── assets/         # Images and other assets
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── styles/         # CSS and styling
│   │   ├── utils/          # Utility functions
│   │   ├── App.jsx         # Main application component
│   │   └── main.jsx        # Entry point
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js      # Vite configuration
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## 🔄 API Endpoints

### Document Management

- `POST /upload-doc`: Upload and index a PDF document
- `GET /documents`: List all indexed documents
- `POST /delete-doc`: Remove a document from the index

### Chat and Query

- `POST /chat`: Text-based RAG queries using Gemini models
- `POST /multimodal-chat`: Process queries with optional image input (OpenAI for image description, Gemini for RAG)

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python -m api.test_hybrid
```

## 🔧 Supported Models

### Gemini Models (Used for RAG and Embeddings)

- gemini-2.0-flash - Faster model, good for most queries
- gemini-2.0-pro - More powerful model for complex queries

### OpenAI Models (Used ONLY for Image Descriptions)

- gpt-4o-mini - Used for generating image descriptions
- gpt-4o - Available but not recommended due to higher cost

## 📊 Token Usage Logging

The system tracks token usage for all model interactions:

- **Input Tokens**: Number of tokens in the prompt/query
- **Output Tokens**: Number of tokens in the model's response
- **Total Tokens**: Sum of input and output tokens
- **Model**: Which model was used for the operation
- **Operation Type**: What type of operation was performed (embedding, RAG, image description)

All token usage is logged to `logs/token_usage.log` for monitoring and cost analysis.

## 📝 Usage Examples

### Upload a Document

```bash
curl -X POST -F "file=@sample.pdf" http://localhost:8000/upload-doc
```

### Text Query (Using Gemini)

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?", "model": "gemini-2.0-flash"}' \
  http://localhost:8000/chat
```

### Multimodal Query with Image

```bash
curl -X POST \
  -F "question=What's in this image?" \
  -F "model=gemini-2.0-flash" \
  -F "image=@sample_image.jpg" \
  http://localhost:8000/multimodal-chat
```

## 📄 License

This project is licensed under the terms of the license included in the repository.
