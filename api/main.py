"""
Stride RAG API - Main Application

This is the main file for the Stride RAG system. It handles:
- Document uploads and processing (including text extraction and image-to-text conversion)
- Text-based questions and answers (which can retrieve information from both document text and image descriptions)
- Document management (listing and deleting)
- Chat history tracking

Available endpoints:
- POST /upload-doc: Upload and process a PDF document (extracts both text and images)
- POST /chat: Ask text-based questions about documents using Gemini
- GET /documents: Get a list of all uploaded documents
- POST /delete-doc: Remove a document
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
from langchain_utils import get_rag_chain, estimate_gemini_tokens
from db_utils import get_chat_history, insert_application_logs, insert_document_record, delete_document_record, get_all_documents
from logger import api_logger, error_logger, PerformanceTimer, app_logger, log_token_usage
import uuid
import shutil
import os
import time

# Create the FastAPI application
app = FastAPI(title="Stride RAG API",
              description="A system that answers questions based on your documents",
              version="1.0.0")

# Allow web browsers to connect to our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization",
                   "Accept", "X-Requested-With", "Origin"],
)


# Handle any unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unexpected errors and return a friendly error message.
    This helps prevent exposing sensitive error details to users.
    """
    # Create a unique ID for this error to help with troubleshooting
    error_id = str(uuid.uuid4())
    error_logger.error(f"Error ID {error_id}: {str(exc)}", exc_info=True)

    # Return a user-friendly error message
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Something went wrong",
            "error_id": error_id,
            "detail": str(exc)
        }
    )


# Log all API requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Track and log all API requests, including timing information.
    This helps with monitoring and troubleshooting.
    """
    # Create a unique ID for this request
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Log when the request starts
    api_logger.info(
        f"Request {request_id} started: {request.method} {request.url.path}")
    app_logger.info(f"Processing request: {request.method} {request.url.path}")

    try:
        # Process the request
        response = await call_next(request)

        # Log when the request completes successfully
        process_time = time.time() - start_time
        api_logger.info(
            f"Request {request_id} completed: Status {response.status_code} in {process_time:.2f}s")
        app_logger.info(
            f"Request completed with status {response.status_code} in {process_time:.2f}s")

        return response
    except Exception as e:
        # Log when the request fails
        process_time = time.time() - start_time
        error_logger.error(
            f"Request {request_id} failed after {process_time:.2f}s: {str(e)}", exc_info=True)
        app_logger.error(f"Request failed: {str(e)}")
        raise


@app.post("/upload-doc")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a PDF document.

    This function:
    1. Saves the uploaded file temporarily
    2. Extracts text and images from the PDF
    3. Converts images to text descriptions using OpenAI
    4. Stores both the text content and image descriptions for future searching
    5. Cleans up the temporary file
    """
    with PerformanceTimer(app_logger, f"upload_file:{file.filename}"):
        try:
            # Save the file temporarily
            temp_path = f"temp_{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            app_logger.info(f"File saved temporarily: {temp_path}")

            # Add the document to our database
            file_id = insert_document_record(file.filename)
            app_logger.info(f"Document added to database with ID: {file_id}")

            # Process the document content
            # This uses OpenAI for image descriptions and Gemini for embeddings
            if index_document_to_chroma(temp_path, file_id):
                app_logger.info(
                    f"Document processed successfully: {file.filename} (ID: {file_id})")
                return {"message": "Document uploaded and processed successfully", "file_id": file_id}
            else:
                app_logger.error(
                    f"Failed to process document: {file.filename}")
                delete_document_record(file_id)
                raise HTTPException(500, "Failed to process document")

        except Exception as e:
            error_logger.error(
                f"Error uploading document {file.filename}: {str(e)}", exc_info=True)
            app_logger.error(f"Upload error: {str(e)}")
            raise HTTPException(500, f"Upload error: {str(e)}")
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                app_logger.info(f"Temporary file removed: {temp_path}")


@app.post("/chat")
async def chat_endpoint(query: QueryInput) -> QueryResponse:
    """
    Answer text-based questions about uploaded documents using Gemini models.

    This function:
    1. Gets any previous conversation history
    2. Searches for relevant information in the documents (including both text content and image descriptions)
    3. Generates an answer based on the found information using Gemini
    4. Saves the conversation for future context
    """
    with PerformanceTimer(app_logger, f"chat_endpoint:{query.model.value}"):
        # Create or use the provided session ID
        session_id = query.session_id or str(uuid.uuid4())

        # Ensure we're using a Gemini model
        original_model = query.model.value
        model_name = original_model
        if not model_name.startswith("gemini"):
            model_name = "gemini-2.0-flash"  # Default to Gemini Flash
            app_logger.warning(
                f"Non-Gemini model requested ({original_model}). Using {model_name} for RAG.")

        app_logger.info(
            f"Chat request: session={session_id}, model={model_name}")

        try:
            # Get previous conversation history
            history = get_chat_history(session_id)
            app_logger.info(f"Found {len(history)//2} previous messages")

            # Search documents and generate an answer using Gemini
            app_logger.info(
                f"Processing question with Gemini: '{query.question[:50]}...'")
            # This ensures Gemini is used
            rag_chain = get_rag_chain(model_name)
            result = rag_chain.invoke({
                "input": query.question,
                "chat_history": history
            })

            # Estimate and log token usage for Gemini
            estimate_gemini_tokens(result, model_name, "rag_chat")

            # Save this conversation
            insert_application_logs(
                session_id=session_id,
                user_query=query.question,
                gpt_response=result["answer"],
                model=model_name
            )
            app_logger.info(f"Conversation saved: session={session_id}")

            # Return the answer
            return QueryResponse(
                answer=result["answer"],
                session_id=session_id,
                model=query.model  # Keep the original model in the response
            )

        except Exception as e:
            error_logger.error(
                f"Error answering question: {str(e)}", exc_info=True)
            app_logger.error(f"Error answering question: {str(e)}")
            raise HTTPException(500, f"Error: {str(e)}")


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """
    Get a list of all uploaded documents.

    This function retrieves information about all documents
    that have been uploaded to the system.
    """
    with PerformanceTimer(app_logger, "list_documents"):
        try:
            # Get all documents from the database
            documents = get_all_documents()
            app_logger.info(f"Found {len(documents)} documents")
            return documents
        except Exception as e:
            error_logger.error(
                f"Error listing documents: {str(e)}", exc_info=True)
            app_logger.error(f"Error listing documents: {str(e)}")
            raise HTTPException(500, f"Error retrieving documents: {str(e)}")


@app.post("/delete-doc")
async def delete_document(req: DeleteFileRequest):
    """
    Delete a document from the system.

    This function:
    1. Removes the document from the search database
    2. Removes the document record from the system
    """
    with PerformanceTimer(app_logger, f"delete_document:{req.file_id}"):
        try:
            app_logger.info(f"Deleting document with ID: {req.file_id}")

            # Remove from search database
            search_deleted = delete_doc_from_chroma(req.file_id)

            # Remove from document records
            db_deleted = delete_document_record(req.file_id)

            if search_deleted and db_deleted:
                app_logger.info(
                    f"Document deleted successfully: ID {req.file_id}")
                return {"message": "Document deleted"}

            error_logger.error(
                f"Failed to delete document ID {req.file_id}: Search={search_deleted}, Database={db_deleted}")
            app_logger.error(f"Failed to delete document ID {req.file_id}")
            raise HTTPException(500, "Failed to delete document")
        except Exception as e:
            error_logger.error(
                f"Error deleting document {req.file_id}: {str(e)}", exc_info=True)
            app_logger.error(f"Error deleting document: {str(e)}")
            raise HTTPException(500, f"Error: {str(e)}")


def run_app():
    """
    Start the application server.

    This function starts the web server that hosts the API.
    It's used when running the application from the command line.
    """
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)


# Start the application if this file is run directly
if __name__ == "__main__":
    run_app()
