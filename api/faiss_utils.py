from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Dict, Tuple
from langchain_core.documents import Document
import fitz
import pdfplumber
import google.generativeai as genai
import os
import base64
from datetime import datetime
import traceback
import shutil
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from logger import model_logger, error_logger, PerformanceTimer

load_dotenv()

model_logger.info("Configuring API clients")
genai.configure(api_key=os.getenv("GEMINI_KEY"))

faiss_db_path = "./faiss_db"
os.makedirs(faiss_db_path, exist_ok=True)
model_logger.info(f"FAISS DB path: {faiss_db_path}")

collection_path = os.path.join(faiss_db_path, "document_collection")
os.makedirs(collection_path, exist_ok=True)

file_id_mapping = {}

try:
    embedding_function = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_KEY"),
        task_type="retrieval_document"
    )
    model_logger.info("Embedding function initialized")
except Exception as e:
    error_logger.error(f"Failed to initialize embedding function: {str(e)}", exc_info=True)
    raise

try:
    if os.path.exists(os.path.join(collection_path, "index.faiss")):
        model_logger.info("Loading existing FAISS index")
        vectorstore = FAISS.load_local(
            collection_path,
            embedding_function,
            allow_dangerous_deserialization=True
        )
        model_logger.info("FAISS vector store loaded")
    else:
        model_logger.info("Creating new FAISS vector store")
        vectorstore = FAISS.from_documents(
            [Document(page_content="Initialization document", metadata={"init": True})],
            embedding_function
        )
        vectorstore.save_local(collection_path)
        model_logger.info("New FAISS vector store initialized")
except Exception as e:
    error_logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
    raise


def extract_images_pymupdf(pdf_path: str, output_dir: str) -> List[Dict]:
    with PerformanceTimer(model_logger, f"extract_images_pymupdf:{os.path.basename(pdf_path)}"):
        images = []
        os.makedirs(output_dir, exist_ok=True)

        try:
            if not os.path.exists(pdf_path):
                error_logger.error(f"PDF file does not exist: {pdf_path}")
                return []

            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                error_logger.error(f"PDF file is empty: {pdf_path}")
                return []

            _, file_extension = os.path.splitext(pdf_path)
            if file_extension.lower() != '.pdf':
                error_logger.error(f"File is not a PDF: {pdf_path}")
                return []

            pdf_document = fitz.open(pdf_path)
            
            if len(pdf_document) == 0:
                error_logger.error(f"PDF has no pages: {pdf_path}")
                return []

            for page_num in range(len(pdf_document)):
                try:
                    page = pdf_document[page_num]
                    image_list = page.get_images(full=True)

                    if not image_list:
                        continue

                    for img_index, img in enumerate(image_list):
                        try:
                            xref = img[0]
                            base_image = pdf_document.extract_image(xref)
                            image_bytes = base_image["image"]

                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            image_filename = f"page{page_num+1}_img{img_index+1}_{timestamp}.png"
                            image_path = os.path.join(output_dir, image_filename)

                            with open(image_path, "wb") as img_file:
                                img_file.write(image_bytes)

                            images.append({
                                'path': image_path,
                                'page': page_num + 1,
                                'index': img_index + 1
                            })
                        except Exception as img_error:
                            error_logger.error(f"Error extracting image {img_index+1} from page {page_num+1}: {str(img_error)}", exc_info=True)
                except Exception as page_error:
                    error_logger.error(f"Error processing page {page_num+1} for images: {str(page_error)}", exc_info=True)

            return images

        except Exception as e:
            error_logger.error(f"Error extracting images from {pdf_path}: {str(e)}", exc_info=True)
            return []


def extract_text_pdfplumber(pdf_path: str) -> List[Dict]:
    with PerformanceTimer(model_logger, f"extract_text_pdfplumber:{os.path.basename(pdf_path)}"):
        texts = []
        try:
            if not os.path.exists(pdf_path):
                error_logger.error(f"PDF file does not exist: {pdf_path}")
                return []

            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                error_logger.error(f"PDF file is empty: {pdf_path}")
                return []

            _, file_extension = os.path.splitext(pdf_path)
            if file_extension.lower() != '.pdf':
                error_logger.error(f"File is not a PDF: {pdf_path}")
                return []

            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    error_logger.error(f"PDF has no pages: {pdf_path}")
                    return []

                for page_num, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            texts.append({
                                'content': text,
                                'page': page_num + 1,
                                'text': text
                            })
                    except Exception as page_error:
                        error_logger.error(f"Error extracting text from page {page_num+1}: {str(page_error)}", exc_info=True)

            if not texts:
                error_logger.error(f"No text could be extracted from {pdf_path}")
                return []

            return texts

        except Exception as e:
            error_logger.error(f"Error extracting text from {pdf_path}: {str(e)}", exc_info=True)
            return []


def resize_image(image_path: str, max_width: int = 800, max_height: int = 800, quality: int = 85) -> bytes:
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            if img.mode == 'RGBA':
                img = img.convert('RGB')

            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            return buffer.getvalue()
    except Exception as e:
        error_logger.error(f"Error resizing image {image_path}: {str(e)}", exc_info=True)
        with open(image_path, 'rb') as img_file:
            return img_file.read()


def get_image_summaries(images: List[Dict]) -> List[Document]:
    with PerformanceTimer(model_logger, f"get_image_summaries:{len(images)} images"):
        summaries = []
        for img in images:
            try:
                image_bytes = resize_image(img['path'])
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                pil_image = Image.open(BytesIO(image_bytes))

                response = model.generate_content([
                    "You are a detailed image analyzer. Describe this image comprehensively, focusing on any text, diagrams, charts, or important visual elements.",
                    pil_image
                ])
                summary = response.text

                print(summary)

                doc = Document(
                    page_content=f"IMAGE: {summary}",
                    metadata={
                        'page': img['page'],
                        'type': 'image',
                        'image_path': img['path']
                    }
                )
                summaries.append(doc)

            except Exception as e:
                error_logger.error(f"Error generating summary for image {img['path']}: {str(e)}", exc_info=True)

        return summaries


def index_document_to_faiss(file_path: str, file_id: int) -> bool:
    with PerformanceTimer(model_logger, f"index_document:{os.path.basename(file_path)}"):
        try:
            image_dir = os.path.join(faiss_db_path, "extracted_images")
            os.makedirs(image_dir, exist_ok=True)

            texts = extract_text_pdfplumber(file_path)
            images = extract_images_pymupdf(file_path, image_dir)

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " "]
            )

            text_docs = [
                Document(
                    page_content=text['content'],
                    metadata={
                        'page': text['page'],
                        'file_id': file_id,
                        'type': 'text',
                        'source': file_path
                    }
                ) for text in texts
            ]
            text_chunks = text_splitter.split_documents(text_docs)

            image_summaries = get_image_summaries(images)
            for doc in image_summaries:
                doc.metadata.update({'file_id': file_id})

            all_docs = text_chunks + image_summaries

            if all_docs:
                vectorstore.add_documents(all_docs)
                vectorstore.save_local(collection_path)
                file_id_mapping[file_id] = all_docs
                return True

            return False

        except Exception as e:
            error_logger.error(f"Indexing error for {file_path}: {str(e)}", exc_info=True)
            return False


def delete_doc_from_faiss(file_id: int) -> bool:
    with PerformanceTimer(model_logger, f"delete_from_faiss:{file_id}"):
        try:
            all_docs = []
            for doc_file_id, docs in file_id_mapping.items():
                if doc_file_id != file_id:
                    all_docs.extend(docs)

            if not all_docs:
                all_docs = [Document(page_content="Initialization document", metadata={"init": True})]

            new_vectorstore = FAISS.from_documents(all_docs, embedding_function)
            new_vectorstore.save_local(collection_path)

            global vectorstore
            vectorstore = new_vectorstore

            if file_id in file_id_mapping:
                del file_id_mapping[file_id]

            return True

        except Exception as e:
            error_logger.error(f"Deletion error for document ID {file_id}: {str(e)}", exc_info=True)
            return False


def clean_faiss_db_except_current(current_file_id: int, clean_db: bool = False) -> bool:
    try:
        all_ids = list(file_id_mapping.keys())

        for file_id in all_ids:
            if file_id != current_file_id:
                delete_doc_from_faiss(file_id)

                if clean_db:
                    from db_utils import delete_document_record
                    delete_document_record(file_id)

        return True
    except Exception as e:
        error_logger.error(f"Error cleaning FAISS DB: {str(e)}", exc_info=True)
        return False
