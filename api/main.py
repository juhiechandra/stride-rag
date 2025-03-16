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
    with PerformanceTimer(api_logger, f"chat_endpoint:{query.model}"):
        session_id = query.session_id or str(uuid.uuid4())
        api_logger.info(
            f"Chat request: session={session_id}, model={query.model}")

        try:
            # Retrieve chat history
            history = get_chat_history(session_id)
            api_logger.info(
                f"Retrieved chat history: {len(history)//2} messages")

            # Execute RAG chain
            api_logger.info(
                f"Executing RAG chain with query: '{query.question[:50]}...'")
            rag_chain = get_rag_chain(query.model)
            result = rag_chain.invoke({
                "input": query.question,
                "chat_history": history
            })

            # Log interaction
            insert_application_logs(
                session_id=session_id,
                user_query=query.question,
                gpt_response=result["answer"],
                model=query.model
            )
            api_logger.info(f"Interaction logged: session={session_id}")

            return QueryResponse(
                answer=result["answer"],
                session_id=session_id,
                model=query.model
            )

        except Exception as e:
            error_logger.error(
                f"Error processing chat request: {str(e)}", exc_info=True)
            raise HTTPException(500, f"Processing error: {str(e)}")


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
