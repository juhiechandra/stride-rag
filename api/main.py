from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest, DocumentBreakdownRequest, DocumentBreakdownResponse
from faiss_utils import index_document_to_faiss, delete_doc_from_faiss, clean_faiss_db_except_current
from langchain_utils import get_rag_chain
from db_utils import get_chat_history, insert_application_logs, insert_document_record, delete_document_record, get_all_documents
from breakdown import analyze_document
from logger import api_logger, error_logger, PerformanceTimer
import uuid
import shutil
import os
import traceback
import time
import sqlite3

# Create a directory for storing uploaded files
UPLOAD_DIR = "./uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Multimodal RAG API",
              description="A Retrieval Augmented Generation system with multimodal capabilities",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://127.0.0.1:5173"],  # Specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization",
                   "Accept", "X-Requested-With", "Origin"],
)

# Global exception handler


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    error_logger.error(
        f"Unhandled exception ID {error_id}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred",
            "error_id": error_id,
            "detail": str(exc)
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Log request details
    api_logger.info(
        f"Request {request_id} started: {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Log response details
        process_time = time.time() - start_time
        api_logger.info(
            f"Request {request_id} completed: Status {response.status_code} in {process_time:.2f}s")

        return response
    except Exception as e:
        # Log exception details
        process_time = time.time() - start_time
        error_logger.error(
            f"Request {request_id} failed after {process_time:.2f}s: {str(e)}", exc_info=True)
        raise


@app.post("/upload-doc")
async def upload_file(file: UploadFile = File(...)):
    with PerformanceTimer(api_logger, f"upload_file:{file.filename}"):
        try:
            # Save temporary file for indexing
            temp_path = f"temp_{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            api_logger.info(f"Temporary file saved: {temp_path}")

            # Index document
            file_id = insert_document_record(file.filename)
            api_logger.info(f"Document record inserted with ID: {file_id}")

            # Save the file to the permanent storage location
            permanent_path = os.path.join(
                UPLOAD_DIR, f"doc-{file_id}-{file.filename}")
            shutil.copy(temp_path, permanent_path)
            api_logger.info(
                f"File saved to permanent storage: {permanent_path}")

            if index_document_to_faiss(temp_path, file_id):
                api_logger.info(
                    f"Document indexed successfully: {file.filename} (ID: {file_id})")

                # Clean up FAISS DB to only keep the current document
                clean_faiss_db_except_current(file_id, clean_db=True)
                api_logger.info(
                    f"FAISS DB and database cleaned, only document ID {file_id} remains")

                # Clean up temporary file
                os.remove(temp_path)
                api_logger.info(f"Temporary file removed: {temp_path}")

                # Clean up old files in the upload directory (keep only the current one)
                cleanup_uploaded_files(file_id)

                return {"message": "Document indexed successfully", "file_id": file_id}
            else:
                # Clean up if indexing failed
                os.remove(temp_path)
                os.remove(permanent_path)
                api_logger.error(f"Failed to index document: {file.filename}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"message": "Failed to index document"}
                )
        except Exception as e:
            error_id = str(uuid.uuid4())
            error_msg = f"Error uploading file: {str(e)}"
            api_logger.error(f"{error_msg} (ID: {error_id})")
            error_logger.error(
                f"Error ID {error_id}: {error_msg}", exc_info=True)

            # Clean up temporary file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": error_msg, "error_id": error_id}
            )


def cleanup_uploaded_files(current_file_id: int):
    """Remove all uploaded files except the current one."""
    try:
        for filename in os.listdir(UPLOAD_DIR):
            # Skip the current file
            if filename.startswith(f"doc-{current_file_id}-"):
                continue

            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                api_logger.info(f"Removed old uploaded file: {file_path}")
    except Exception as e:
        error_logger.error(
            f"Error cleaning up uploaded files: {str(e)}", exc_info=True)


@app.post("/chat")
async def chat_endpoint(query: QueryInput) -> QueryResponse:
    """
    Process a chat query using RAG.

    Args:
        query: The query input containing the question and chat history.

    Returns:
        A response containing the answer and updated chat history.
    """
    try:
        with PerformanceTimer(api_logger, f"chat_endpoint:{query.question[:30]}"):
            api_logger.info(f"Received chat query: {query.question[:100]}...")

            # Get chat history from database if session_id is provided
            chat_history = []
            if query.session_id:
                api_logger.info(
                    f"Getting chat history for session: {query.session_id}")
                chat_history = get_chat_history(query.session_id)
                api_logger.info(
                    f"Retrieved {len(chat_history)} chat history items")

            # Convert chat history to the format expected by LangChain
            formatted_history = []
            for item in chat_history:
                formatted_history.append(("human", item["question"]))
                formatted_history.append(("ai", item["answer"]))

            # Get RAG chain with specified model and hybrid search option
            use_hybrid_search = query.use_hybrid_search if hasattr(
                query, 'use_hybrid_search') else True
            chain = get_rag_chain(
                model=query.model, use_hybrid_search=use_hybrid_search)

            # Process query
            api_logger.info(f"Processing query with model: {query.model}")
            start_time = time.time()
            response = chain.invoke({
                "input": query.question,
                "chat_history": formatted_history
            })
            end_time = time.time()
            processing_time = end_time - start_time
            api_logger.info(
                f"Query processed in {processing_time:.2f} seconds")

            # Extract answer
            answer = response["answer"]
            api_logger.info(f"Generated answer: {answer[:100]}...")

            # Log to database if session_id is provided
            if query.session_id:
                api_logger.info(
                    f"Logging chat to database for session: {query.session_id}")
                insert_application_logs(
                    session_id=query.session_id,
                    question=query.question,
                    answer=answer,
                    model=query.model,
                    processing_time=processing_time
                )

            # Return response
            return QueryResponse(
                answer=answer,
                processing_time=processing_time,
                model=query.model
            )

    except Exception as e:
        error_msg = f"Error processing chat query: {str(e)}"
        api_logger.error(error_msg)
        error_logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    with PerformanceTimer(api_logger, "list_documents"):
        try:
            documents = get_all_documents()
            api_logger.info(f"Retrieved {len(documents)} documents")
            return documents
        except Exception as e:
            error_logger.error(
                f"Error listing documents: {str(e)}", exc_info=True)
            raise HTTPException(500, f"Error retrieving documents: {str(e)}")


@app.post("/delete-doc")
async def delete_document(req: DeleteFileRequest):
    """Delete a document from the system."""
    with PerformanceTimer(api_logger, f"delete_document:{req.file_id}"):
        try:
            # Get the document filename before deleting the record
            conn = sqlite3.connect("rag_app.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filename FROM document_store WHERE id = ?", (req.file_id,))
            document = cursor.fetchone()
            conn.close()

            if not document:
                api_logger.error(f"Document with ID {req.file_id} not found")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "message": f"Document with ID {req.file_id} not found"}
                )

            filename = document["filename"]

            # Delete from FAISS
            if delete_doc_from_faiss(req.file_id):
                api_logger.info(
                    f"Document removed from FAISS: ID {req.file_id}")
            else:
                api_logger.warning(
                    f"Failed to remove document from FAISS: ID {req.file_id}")

            # Delete from database
            if delete_document_record(req.file_id):
                api_logger.info(
                    f"Document record deleted: ID {req.file_id}")
            else:
                api_logger.warning(
                    f"Failed to delete document record: ID {req.file_id}")

            # Delete the file from the upload directory if it exists
            upload_path = os.path.join(
                UPLOAD_DIR, f"doc-{req.file_id}-{filename}")
            if os.path.exists(upload_path):
                os.remove(upload_path)
                api_logger.info(
                    f"Deleted file from upload directory: {upload_path}")

            return {"message": f"Document with ID {req.file_id} deleted"}
        except Exception as e:
            error_id = str(uuid.uuid4())
            error_msg = f"Error deleting document: {str(e)}"
            api_logger.error(f"{error_msg} (ID: {error_id})")
            error_logger.error(
                f"Error ID {error_id}: {error_msg}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": error_msg, "error_id": error_id}
            )


@app.post("/document/analyze", response_model=DocumentBreakdownResponse)
async def analyze_document_endpoint(req: DocumentBreakdownRequest):
    """Analyze a document and generate a structured breakdown."""
    with PerformanceTimer(api_logger, f"analyze_document:{req.file_id}"):
        try:
            # Validate file_id
            conn = sqlite3.connect("rag_app.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filename FROM document_store WHERE id = ?", (req.file_id,))
            document = cursor.fetchone()
            conn.close()

            if not document:
                error_msg = f"Document with ID {req.file_id} not found in database"
                api_logger.error(error_msg)
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"status": "error", "message": error_msg}
                )

            # Check if file exists in upload directory
            filename = document["filename"]
            upload_path = os.path.join(
                UPLOAD_DIR, f"doc-{req.file_id}-{filename}")

            if not os.path.exists(upload_path):
                error_msg = f"Document file not found at expected path: {upload_path}"
                api_logger.error(error_msg)
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"status": "error", "message": error_msg}
                )

            # Log file details
            file_size = os.path.getsize(upload_path)
            api_logger.info(f"Document file size: {file_size} bytes")

            # Call the analyze_document function
            api_logger.info(
                f"Calling analyze_document for file ID {req.file_id} with model {req.model}")
            breakdown = analyze_document(req.file_id, req.model)

            # Check if there was an error
            if "error" in breakdown:
                error_msg = breakdown["error"]
                api_logger.error(error_msg)
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"status": "error", "message": error_msg}
                )

            # Validate the breakdown structure
            try:
                # Check if all required fields are present
                required_fields = ["major_components",
                                   "diagrams", "api_contracts", "pii_data"]
                missing_fields = [
                    field for field in required_fields if field not in breakdown]

                if missing_fields:
                    error_msg = f"Breakdown response is missing required fields: {', '.join(missing_fields)}"
                    api_logger.error(error_msg)
                    return JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"status": "error", "message": error_msg}
                    )

                api_logger.info(
                    f"Document {req.file_id} analyzed successfully")
                return breakdown
            except Exception as validation_error:
                error_msg = f"Error validating breakdown response: {str(validation_error)}"
                api_logger.error(error_msg)
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"status": "error", "message": error_msg}
                )
        except Exception as e:
            error_id = str(uuid.uuid4())
            error_msg = f"Error analyzing document: {str(e)}"
            api_logger.error(f"{error_msg} (ID: {error_id})")
            error_logger.error(
                f"Error ID {error_id}: {error_msg}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error",
                         "message": error_msg, "error_id": error_id}
            )


@app.post("/cleanup-documents")
async def cleanup_documents():
    """Clean up all documents from the system."""
    with PerformanceTimer(api_logger, "cleanup_documents"):
        try:
            # Get all documents
            documents = get_all_documents()

            # Delete each document
            for doc in documents:
                file_id = doc["id"]
                filename = doc["filename"]

                # Delete from FAISS
                delete_doc_from_faiss(file_id)

                # Delete from database
                delete_document_record(file_id)

                # Delete from upload directory
                upload_path = os.path.join(
                    UPLOAD_DIR, f"doc-{file_id}-{filename}")
                if os.path.exists(upload_path):
                    os.remove(upload_path)
                    api_logger.info(
                        f"Deleted file from upload directory: {upload_path}")

            # Clean up all files in the upload directory
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    api_logger.info(
                        f"Removed file from upload directory: {file_path}")

            api_logger.info("All documents cleaned up successfully")
            return {"message": "All documents cleaned up successfully"}
        except Exception as e:
            error_id = str(uuid.uuid4())
            error_msg = f"Error cleaning up documents: {str(e)}"
            api_logger.error(f"{error_msg} (ID: {error_id})")
            error_logger.error(
                f"Error ID {error_id}: {error_msg}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": error_msg, "error_id": error_id}
            )
