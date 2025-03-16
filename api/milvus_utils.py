from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_milvus import Milvus
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Dict, Tuple
from langchain_core.documents import Document
import fitz  # PyMuPDF
import pdfplumber
import google.generativeai as genai
from openai import OpenAI
import os
import base64
from datetime import datetime
import traceback
from pymilvus import connections, Collection, utility
from pymilvus.exceptions import MilvusException
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from logger import model_logger, error_logger, PerformanceTimer
import time
import socket

# Load environment variables
load_dotenv()

# Configure APIs
model_logger.info("Configuring API clients")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Milvus connection settings
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = "document_collection"
DIMENSION = 768  # Dimension for Gemini embedding-001 model

# Global variables
milvus_available = False
vectorstore = None
embedding_function = None


def is_port_open(host, port, timeout=2):
    """Check if a port is open on the given host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0
    except Exception as e:
        error_logger.error(f"Error checking port {port} on {host}: {str(e)}")
        return False


def connect_to_milvus(max_retries=3, retry_interval=5):
    """Connect to Milvus with retries."""
    global milvus_available

    if not is_port_open(MILVUS_HOST, MILVUS_PORT):
        error_logger.error(
            f"Milvus server not available at {MILVUS_HOST}:{MILVUS_PORT}")
        milvus_available = False
        return False

    for attempt in range(max_retries):
        try:
            connections.connect(
                alias="default",
                host=MILVUS_HOST,
                port=MILVUS_PORT,
                timeout=10
            )
            model_logger.info(
                f"Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
            milvus_available = True
            return True
        except MilvusException as e:
            error_logger.error(
                f"Connection attempt {attempt+1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
    milvus_available = False
    return False


# Initialize embedding function
try:
    embedding_function = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        task_type="retrieval_document"
    )
    model_logger.info("Embedding function initialized")
except Exception as e:
    error_logger.error(f"Embedding init failed: {str(e)}")
    embedding_function = None

# Connect to Milvus
connect_to_milvus()


def init_milvus_collection():
    """Initialize or get Milvus collection."""
    global milvus_available

    if not milvus_available:
        return None

    try:
        if not utility.has_collection(COLLECTION_NAME):
            from pymilvus import CollectionSchema, FieldSchema, DataType

            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR,
                            is_primary=True, max_length=100, auto_id=True),
                FieldSchema(name="file_id", dtype=DataType.INT64,
                            is_nullable=True),
                FieldSchema(name="page", dtype=DataType.INT64,
                            is_nullable=True),
                FieldSchema(name="type", dtype=DataType.VARCHAR,
                            max_length=20, is_nullable=True),
                FieldSchema(name="source", dtype=DataType.VARCHAR,
                            max_length=2000, is_nullable=True),
                FieldSchema(name="content", dtype=DataType.VARCHAR,
                            max_length=65535, is_nullable=True),
                FieldSchema(name="vector",
                            dtype=DataType.FLOAT_VECTOR, dim=DIMENSION)
            ]

            schema = CollectionSchema(fields=fields, enable_dynamic_field=True)
            collection = Collection(name=COLLECTION_NAME, schema=schema)

            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 8, "efConstruction": 64}
            }
            collection.create_index(
                field_name="vector", index_params=index_params)
            collection.load()
            model_logger.info(f"Created new collection: {COLLECTION_NAME}")
        else:
            collection = Collection(COLLECTION_NAME)
            collection.load()
            model_logger.info(f"Using existing collection: {COLLECTION_NAME}")

        return collection
    except Exception as e:
        error_logger.error(f"Collection init failed: {str(e)}")
        milvus_available = False
        return None


def init_vectorstore():
    """Initialize the vector store."""
    global vectorstore, milvus_available

    if not milvus_available or not embedding_function:
        return None

    try:
        collection = init_milvus_collection()
        if not collection:
            return None

        vectorstore = Milvus(
            embedding_function=embedding_function,
            collection_name=COLLECTION_NAME,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
            text_field="content",
            vector_field="vector",
            metadata_field="metadata",
            auto_id=True
        )
        model_logger.info("Vector store initialized")
        return vectorstore
    except Exception as e:
        error_logger.error(f"Vector store init failed: {str(e)}")
        milvus_available = False
        return None


# Initialize vectorstore
if milvus_available:
    vectorstore = init_vectorstore()


def extract_images_pymupdf(pdf_path: str, output_dir: str) -> List[Dict]:
    """Extract images from PDF using PyMuPDF"""
    with PerformanceTimer(model_logger, f"extract_images_pymupdf:{os.path.basename(pdf_path)}"):
        images = []
        os.makedirs(output_dir, exist_ok=True)

        try:
            pdf_document = fitz.open(pdf_path)
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_filename = f"page{page_num+1}_img{img_index+1}.{base_image['ext']}"
                        image_path = os.path.join(output_dir, image_filename)

                        with open(image_path, "wb") as f:
                            f.write(image_bytes)

                        images.append({
                            'page': page_num + 1,
                            'file_path': image_path,
                            'base64': base64.b64encode(image_bytes).decode('utf-8')
                        })
                    except Exception as e:
                        error_logger.error(f"Image processing error: {str(e)}")
            pdf_document.close()
        except Exception as e:
            error_logger.error(f"PDF processing error: {str(e)}")

        return images


def extract_text_pdfplumber(pdf_path: str) -> List[Dict]:
    """Extract text from PDF using pdfplumber"""
    with PerformanceTimer(model_logger, f"extract_text_pdfplumber:{os.path.basename(pdf_path)}"):
        texts = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        texts.append({'content': text, 'page': page_num + 1})
        except Exception as e:
            error_logger.error(f"Text extraction error: {str(e)}")
        return texts


def get_image_summaries(images: List[Dict]) -> List[Document]:
    """Generate image summaries using OpenAI"""
    with PerformanceTimer(model_logger, f"get_image_summaries:{len(images)} images"):
        summaries = []
        MAX_IMAGES = 10

        for i, image in enumerate(images[:MAX_IMAGES]):
            try:
                img_bytes = base64.b64decode(image['base64'])
                img = Image.open(BytesIO(img_bytes))
                img.thumbnail((800, 800))
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                processed_base64 = base64.b64encode(
                    buffer.getvalue()).decode('utf-8')

                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text",
                                "text": "Describe this image for document retrieval:"},
                            {"type": "image_url",
                             "image_url": {"url": f"data:image/jpeg;base64,{processed_base64}"}}
                        ]
                    }],
                    max_tokens=300
                )

                summary = response.choices[0].message.content
                summaries.append(Document(
                    page_content=summary,
                    metadata={
                        'type': 'image',
                        'page': image['page'],
                        'file_path': image['file_path']
                    }
                ))
            except Exception as e:
                error_logger.error(f"Image summary error: {str(e)}")

        return summaries


def index_document_to_milvus(file_path: str, file_id: int) -> bool:
    """Main indexing function"""
    global milvus_available, vectorstore

    if not milvus_available:
        if connect_to_milvus():
            vectorstore = init_vectorstore()
        else:
            return False

    with PerformanceTimer(model_logger, f"index_document:{os.path.basename(file_path)}"):
        try:
            image_dir = os.path.join("extracted_images")
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
                doc.metadata['file_id'] = file_id

            all_docs = text_chunks + image_summaries
            if all_docs:
                vectorstore.add_documents(all_docs)
                return True
            return False

        except Exception as e:
            error_logger.error(f"Indexing error: {str(e)}")
            return False


def delete_doc_from_milvus(file_id: int) -> bool:
    """Delete documents by file_id"""
    global milvus_available

    if not milvus_available:
        return False

    with PerformanceTimer(model_logger, f"delete_from_milvus:{file_id}"):
        try:
            collection = Collection(COLLECTION_NAME)
            collection.delete(expr=f"file_id == {file_id}")
            return True
        except Exception as e:
            error_logger.error(f"Deletion error: {str(e)}")
            return False
