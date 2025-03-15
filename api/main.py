from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
from langchain_utils import get_rag_chain
from db_utils import get_chat_history, insert_application_logs, insert_document_record, delete_document_record, get_all_documents
from logger import api_logger, error_logger, PerformanceTimer
import uuid
import shutil
import os
from PIL import Image
from io import BytesIO
import base64
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

            if index_document_to_chroma(temp_path, file_id):
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
    with PerformanceTimer(api_logger, f"chat_endpoint:{query.model.value}"):
        session_id = query.session_id or str(uuid.uuid4())
        api_logger.info(
            f"Chat request: session={session_id}, model={query.model.value}")

        try:
            # Retrieve chat history
            history = get_chat_history(session_id)
            api_logger.info(
                f"Retrieved chat history: {len(history)//2} messages")

            # Execute RAG chain
            api_logger.info(
                f"Executing RAG chain with query: '{query.question[:50]}...'")
            rag_chain = get_rag_chain(query.model.value)
            result = rag_chain.invoke({
                "input": query.question,
                "chat_history": history
            })

            # Log interaction
            insert_application_logs(
                session_id=session_id,
                user_query=query.question,
                gpt_response=result["answer"],
                model=query.model.value
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
            chroma_deleted = delete_doc_from_chroma(req.file_id)
            db_deleted = delete_document_record(req.file_id)

            if chroma_deleted and db_deleted:
                api_logger.info(
                    f"Document deleted successfully: ID {req.file_id}")
                return {"message": "Document deleted"}

            error_logger.error(
                f"Deletion failed for document ID {req.file_id}: Chroma={chroma_deleted}, DB={db_deleted}")
            raise HTTPException(500, "Deletion failed")
        except Exception as e:
            error_logger.error(
                f"Error deleting document {req.file_id}: {str(e)}", exc_info=True)
            raise HTTPException(500, f"Deletion error: {str(e)}")


@app.post("/multimodal-chat")
async def multimodal_chat_endpoint(
    question: str = Form(...),
    session_id: Optional[str] = Form(None),
    model: str = Form("gemini-2.0-flash"),
    image: Optional[UploadFile] = File(None)
):
    current_session_id = session_id or str(uuid.uuid4())
    operation_name = f"multimodal_chat:{current_session_id}:{model}"

    with PerformanceTimer(api_logger, operation_name):
        try:
            api_logger.info(
                f"Multimodal chat request: session={current_session_id}, model={model}, has_image={image is not None}")

            # Retrieve chat history
            history = get_chat_history(current_session_id)
            api_logger.info(
                f"Retrieved chat history: {len(history)//2} messages")

            # Process image if provided
            image_content = None
            if image:
                api_logger.info(f"Processing image: {image.filename}")
                # Read and process image
                image_bytes = await image.read()
                img = Image.open(BytesIO(image_bytes))

                # Resize image to reduce token count
                max_dimension = 800
                width, height = img.size
                api_logger.info(f"Original image dimensions: {width}x{height}")

                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))

                # Resize and compress
                img = img.resize((new_width, new_height), Image.LANCZOS)
                api_logger.info(
                    f"Resized image dimensions: {new_width}x{new_height}")

                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                buffer.seek(0)

                # Convert to base64
                image_content = base64.b64encode(
                    buffer.getvalue()).decode('utf-8')
                api_logger.info(
                    f"Image processed: original size={len(image_bytes)}, compressed size={len(buffer.getvalue())}")

            # For direct model access (bypassing RAG for image queries)
            if image_content and (model.startswith("gpt") or model.startswith("gemini")):
                from chroma_utils import client as openai_client
                import google.generativeai as genai

                if model.startswith("gpt"):
                    # Use OpenAI for image processing
                    api_logger.info(
                        f"Using OpenAI for image processing: model={model}")
                    start_time = time.time()

                    response = openai_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system",
                                "content": "You are a helpful assistant that can analyze images."},
                            {"role": "user", "content": [
                                {"type": "text", "text": question},
                                {"type": "image_url", "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_content}"}}
                            ]}
                        ],
                        max_tokens=1000
                    )

                    elapsed_time = time.time() - start_time
                    api_logger.info(
                        f"OpenAI response received in {elapsed_time:.2f}s")
                    answer = response.choices[0].message.content

                elif model.startswith("gemini"):
                    # Use Gemini for image processing
                    api_logger.info(
                        f"Using Gemini for image processing: model={model}")
                    start_time = time.time()

                    gemini_model = genai.GenerativeModel(model)
                    response = gemini_model.generate_content([
                        question,
                        {"mime_type": "image/jpeg", "data": buffer.getvalue()}
                    ])

                    elapsed_time = time.time() - start_time
                    api_logger.info(
                        f"Gemini response received in {elapsed_time:.2f}s")
                    answer = response.text

                # Log interaction
                insert_application_logs(
                    session_id=current_session_id,
                    user_query=f"[Image Query] {question}",
                    gpt_response=answer,
                    model=model
                )
                api_logger.info(
                    f"Multimodal interaction logged: session={current_session_id}")

                return {
                    "answer": answer,
                    "session_id": current_session_id,
                    "model": model
                }

            # Standard RAG flow for text-only queries
            api_logger.info(f"Using standard RAG flow: model={model}")
            rag_chain = get_rag_chain(model)
            result = rag_chain.invoke({
                "input": question,
                "chat_history": history
            })

            # Log interaction
            insert_application_logs(
                session_id=current_session_id,
                user_query=question,
                gpt_response=result["answer"],
                model=model
            )
            api_logger.info(
                f"Text interaction logged: session={current_session_id}")

            return {
                "answer": result["answer"],
                "session_id": current_session_id,
                "model": model
            }

        except Exception as e:
            error_msg = f"Multimodal processing error: {str(e)}"
            error_logger.error(error_msg, exc_info=True)
            raise HTTPException(500, error_msg)
