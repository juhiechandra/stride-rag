from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from faiss_utils import index_document_to_faiss, delete_doc_from_faiss
from langchain_utils import get_rag_chain
from db_utils import get_chat_history, insert_application_logs, insert_document_record, delete_document_record, get_all_documents
from logger import api_logger, error_logger, PerformanceTimer
import uuid
import shutil
import os
import traceback
import time

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
            # Save temporary file
            temp_path = f"temp_{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            api_logger.info(f"Temporary file saved: {temp_path}")

            # Index document
            file_id = insert_document_record(file.filename)
            api_logger.info(f"Document record inserted with ID: {file_id}")

            if index_document_to_faiss(temp_path, file_id):
                api_logger.info(
                    f"Document indexed successfully: {file.filename} (ID: {file_id})")
                return {"message": "Document indexed successfully", "file_id": file_id}
            else:
                api_logger.error(
                    f"Indexing failed for document: {file.filename}")
                delete_document_record(file_id)
                raise HTTPException(500, "Indexing failed")

        except Exception as e:
            error_logger.error(
                f"Error uploading document {file.filename}: {str(e)}", exc_info=True)
            raise HTTPException(500, f"Upload error: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                api_logger.info(f"Temporary file removed: {temp_path}")


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
    with PerformanceTimer(api_logger, f"delete_document:{req.file_id}"):
        try:
            api_logger.info(f"Deleting document with ID: {req.file_id}")
            faiss_deleted = delete_doc_from_faiss(req.file_id)
            db_deleted = delete_document_record(req.file_id)

            if faiss_deleted and db_deleted:
                api_logger.info(
                    f"Document deleted successfully: ID {req.file_id}")
                return {"message": "Document deleted"}

            error_logger.error(
                f"Deletion failed for document ID {req.file_id}: FAISS={faiss_deleted}, DB={db_deleted}")
            raise HTTPException(500, "Deletion failed")
        except Exception as e:
            error_logger.error(
                f"Error deleting document {req.file_id}: {str(e)}", exc_info=True)
            raise HTTPException(500, f"Deletion error: {str(e)}")
