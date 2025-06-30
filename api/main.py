from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from faiss_utils import index_document_to_faiss, delete_doc_from_faiss, clean_faiss_db_except_current
from langchain_utils import get_rag_chain
from db_utils import get_chat_history, insert_application_logs, insert_document_record, delete_document_record, get_all_documents
from logger import api_logger, error_logger, PerformanceTimer
import uuid
import shutil
import os
import traceback
import time
import sqlite3

UPLOAD_DIR = "./uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Simple RAG API", description="A simple Retrieval Augmented Generation chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    error_logger.error(f"Unhandled exception ID {error_id}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected error occurred", "error_id": error_id, "detail": str(exc)}
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        return response
    except Exception as e:
        process_time = time.time() - start_time
        error_logger.error(f"Request {request_id} failed after {process_time:.2f}s: {str(e)}", exc_info=True)
        raise


@app.post("/upload-doc")
async def upload_file(file: UploadFile = File(...)):
    with PerformanceTimer(api_logger, f"upload_file:{file.filename}"):
        try:
            temp_path = f"temp_{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_id = insert_document_record(file.filename)
            permanent_path = os.path.join(UPLOAD_DIR, f"doc-{file_id}-{file.filename}")
            shutil.copy(temp_path, permanent_path)

            if index_document_to_faiss(temp_path, file_id):
                clean_faiss_db_except_current(file_id, clean_db=True)
                os.remove(temp_path)
                cleanup_uploaded_files(file_id)
                return {"message": "Document indexed successfully", "file_id": file_id}
            else:
                os.remove(temp_path)
                os.remove(permanent_path)
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"message": "Failed to index document"}
                )
        except Exception as e:
            error_id = str(uuid.uuid4())
            error_logger.error(f"Error ID {error_id}: Error uploading file: {str(e)}", exc_info=True)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": f"Error uploading file: {str(e)}", "error_id": error_id}
            )


def cleanup_uploaded_files(current_file_id: int):
    try:
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(f"doc-{current_file_id}-"):
                continue

            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        error_logger.error(f"Error cleaning up uploaded files: {str(e)}", exc_info=True)


@app.post("/chat")
async def chat_endpoint(query: QueryInput) -> QueryResponse:
    try:
        with PerformanceTimer(api_logger, f"chat_endpoint:{query.question[:30]}"):
            chat_history = []
            if query.session_id:
                chat_history = get_chat_history(query.session_id)

            formatted_history = []
            for item in chat_history:
                formatted_history.append(("human", item["question"]))
                formatted_history.append(("ai", item["answer"]))

            chain = get_rag_chain(model=query.model)

            start_time = time.time()
            response = chain.invoke({
                "input": query.question,
                "chat_history": formatted_history
            })
            processing_time = time.time() - start_time

            answer = response["answer"]

            if query.session_id:
                insert_application_logs(
                    session_id=query.session_id,
                    question=query.question,
                    answer=answer,
                    model=query.model,
                    processing_time=processing_time
                )

            return QueryResponse(
                answer=answer,
                processing_time=processing_time,
                model=query.model
            )

    except Exception as e:
        error_logger.error(f"Error processing chat query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    with PerformanceTimer(api_logger, "list_documents"):
        try:
            documents = get_all_documents()
            return documents
        except Exception as e:
            error_logger.error(f"Error listing documents: {str(e)}", exc_info=True)
            raise HTTPException(500, f"Error retrieving documents: {str(e)}")


@app.post("/delete-doc")
async def delete_document(req: DeleteFileRequest):
    with PerformanceTimer(api_logger, f"delete_document:{req.file_id}"):
        try:
            conn = sqlite3.connect("rag_app.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT filename FROM document_store WHERE id = ?", (req.file_id,))
            document = cursor.fetchone()
            conn.close()

            if not document:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"message": f"Document with ID {req.file_id} not found"}
                )

            filename = document["filename"]

            delete_doc_from_faiss(req.file_id)
            delete_document_record(req.file_id)

            upload_path = os.path.join(UPLOAD_DIR, f"doc-{req.file_id}-{filename}")
            if os.path.exists(upload_path):
                os.remove(upload_path)

            return {"message": f"Document with ID {req.file_id} deleted"}
        except Exception as e:
            error_id = str(uuid.uuid4())
            error_logger.error(f"Error ID {error_id}: Error deleting document: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": f"Error deleting document: {str(e)}", "error_id": error_id}
            )


@app.post("/cleanup-documents")
async def cleanup_documents():
    with PerformanceTimer(api_logger, "cleanup_documents"):
        try:
            documents = get_all_documents()

            for doc in documents:
                file_id = doc["id"]
                filename = doc["filename"]

                delete_doc_from_faiss(file_id)
                delete_document_record(file_id)

                upload_path = os.path.join(UPLOAD_DIR, f"doc-{file_id}-{filename}")
                if os.path.exists(upload_path):
                    os.remove(upload_path)

            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

            return {"message": "All documents cleaned up successfully"}
        except Exception as e:
            error_id = str(uuid.uuid4())
            error_logger.error(f"Error ID {error_id}: Error cleaning up documents: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": f"Error cleaning up documents: {str(e)}", "error_id": error_id}
            )
