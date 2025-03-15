from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
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
import chromadb
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from logger import model_logger, error_logger, PerformanceTimer

# Load environment variables
load_dotenv()

# Configure APIs
model_logger.info("Configuring API clients")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB
chroma_db_path = "./chroma_db"
os.makedirs(chroma_db_path, exist_ok=True)
model_logger.info(f"ChromaDB path: {chroma_db_path}")

try:
    chroma_client = chromadb.PersistentClient(
        path=chroma_db_path,
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True
        )
    )
    model_logger.info("ChromaDB client initialized")
except Exception as e:
    error_logger.error(
        f"Failed to initialize ChromaDB client: {str(e)}", exc_info=True)
    raise

try:
    embedding_function = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        task_type="retrieval_document"
    )
    model_logger.info("Embedding function initialized")
except Exception as e:
    error_logger.error(
        f"Failed to initialize embedding function: {str(e)}", exc_info=True)
    raise

try:
    vectorstore = Chroma(
        client=chroma_client,
        embedding_function=embedding_function,
        collection_name="document_collection"
    )
    model_logger.info("Vector store initialized")
except Exception as e:
    error_logger.error(
        f"Failed to initialize vector store: {str(e)}", exc_info=True)
    raise


def extract_images_pymupdf(pdf_path: str, output_dir: str) -> List[Dict]:
    """Extract images from PDF using PyMuPDF"""
    with PerformanceTimer(model_logger, f"extract_images_pymupdf:{os.path.basename(pdf_path)}"):
        images = []
        os.makedirs(output_dir, exist_ok=True)

        try:
            pdf_document = fitz.open(pdf_path)
            model_logger.info(
                f"PDF opened: {pdf_path} ({len(pdf_document)} pages)")

            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                image_list = page.get_images()
                model_logger.info(
                    f"Found {len(image_list)} images on page {page_num+1}")

                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]

                        # Convert to base64 and save
                        image_base64 = base64.b64encode(
                            image_bytes).decode('utf-8')
                        image_filename = f"page{page_num+1}_img{img_index+1}.{base_image['ext']}"
                        image_path = os.path.join(output_dir, image_filename)

                        with open(image_path, "wb") as f:
                            f.write(image_bytes)

                        images.append({
                            'page': page_num + 1,
                            'file_path': image_path,
                            'base64': image_base64
                        })
                        model_logger.info(
                            f"Extracted image: {image_filename} ({len(image_bytes)} bytes)")
                    except Exception as e:
                        error_msg = f"Error processing image {img_index} on page {page_num+1}: {str(e)}"
                        model_logger.error(error_msg)
                        error_logger.error(error_msg, exc_info=True)

            pdf_document.close()
            model_logger.info(
                f"Extracted {len(images)} images total from {pdf_path}")
        except Exception as e:
            error_msg = f"PDF processing error: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)

        return images


def extract_text_pdfplumber(pdf_path: str) -> List[Dict]:
    """Extract text from PDF using pdfplumber"""
    with PerformanceTimer(model_logger, f"extract_text_pdfplumber:{os.path.basename(pdf_path)}"):
        texts = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                model_logger.info(
                    f"PDF opened with pdfplumber: {pdf_path} ({len(pdf.pages)} pages)")

                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        texts.append({'content': text, 'page': page_num + 1})
                        char_count = len(text)
                        model_logger.info(
                            f"Extracted text from page {page_num+1}: {char_count} characters")
                    else:
                        model_logger.info(
                            f"No text found on page {page_num+1}")

                model_logger.info(
                    f"Extracted text from {len(texts)} pages total")
        except Exception as e:
            error_msg = f"Text extraction error: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)

        return texts


def get_image_summaries(images: List[Dict]) -> List[Document]:
    """Generate image summaries using OpenAI"""
    with PerformanceTimer(model_logger, f"get_image_summaries:{len(images)} images"):
        summaries = []
        MAX_IMAGES = 10  # Limit to avoid token overflow

        model_logger.info(
            f"Processing {min(len(images), MAX_IMAGES)} images for summarization")

        for i, image in enumerate(images[:MAX_IMAGES]):
            with PerformanceTimer(model_logger, f"summarize_image:{i+1}"):
                try:
                    # Process image
                    img_bytes = base64.b64decode(image['base64'])
                    img = Image.open(BytesIO(img_bytes))
                    model_logger.info(
                        f"Processing image {i+1}: original size {img.size}")

                    # Resize and compress
                    img.thumbnail((800, 800))
                    buffer = BytesIO()
                    img.save(buffer, format="JPEG", quality=85)
                    processed_base64 = base64.b64encode(
                        buffer.getvalue()).decode('utf-8')
                    model_logger.info(
                        f"Image {i+1} resized to {img.size}, compressed from {len(img_bytes)} to {len(buffer.getvalue())} bytes")

                    # Generate summary
                    model_logger.info(
                        f"Generating summary for image {i+1} using OpenAI")
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Describe this image in detail for document retrieval:"},
                                {"type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{processed_base64}"}}
                            ]
                        }],
                        max_tokens=300
                    )

                    summary = response.choices[0].message.content
                    model_logger.info(
                        f"Generated summary for image {i+1}: {len(summary)} characters")

                    summaries.append(Document(
                        page_content=summary,
                        metadata={
                            'type': 'image',
                            'page': image['page'],
                            'file_path': image['file_path']
                        }
                    ))
                except Exception as e:
                    error_msg = f"Error processing image {i+1}: {str(e)}"
                    model_logger.error(error_msg)
                    error_logger.error(error_msg, exc_info=True)
                    traceback.print_exc()  # Add detailed error traceback

        model_logger.info(f"Generated {len(summaries)} image summaries total")
        return summaries


def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    """Main indexing function with text and image processing"""
    with PerformanceTimer(model_logger, f"index_document:{os.path.basename(file_path)}"):
        try:
            # Create output directories
            image_dir = os.path.join(chroma_db_path, "extracted_images")
            os.makedirs(image_dir, exist_ok=True)
            model_logger.info(
                f"Starting indexing for document: {file_path} (ID: {file_id})")

            # Extract content
            model_logger.info(f"Extracting text from {file_path}")
            texts = extract_text_pdfplumber(file_path)
            model_logger.info(f"Extracting images from {file_path}")
            images = extract_images_pymupdf(file_path, image_dir)

            # Process text
            model_logger.info(f"Processing {len(texts)} text chunks")
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
            model_logger.info(f"Split text into {len(text_chunks)} chunks")

            # Process images
            model_logger.info(f"Processing {len(images)} images")
            image_summaries = get_image_summaries(images)
            for doc in image_summaries:
                doc.metadata.update({'file_id': file_id})
            model_logger.info(
                f"Generated {len(image_summaries)} image summaries")

            # Combine and store
            all_docs = text_chunks + image_summaries
            model_logger.info(
                f"Indexing {len(all_docs)} total documents to ChromaDB")

            if all_docs:
                vectorstore.add_documents(all_docs)
                model_logger.info(
                    f"Successfully indexed document {file_path} (ID: {file_id})")
                return True

            model_logger.warning(
                f"No content extracted from document {file_path}")
            return False

        except Exception as e:
            error_msg = f"Indexing error for {file_path}: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return False


def delete_doc_from_chroma(file_id: int) -> bool:
    """Delete documents by file_id"""
    with PerformanceTimer(model_logger, f"delete_from_chroma:{file_id}"):
        try:
            model_logger.info(f"Deleting document ID {file_id} from ChromaDB")
            vectorstore._collection.delete(where={"file_id": file_id})
            model_logger.info(
                f"Successfully deleted document ID {file_id} from ChromaDB")
            return True
        except Exception as e:
            error_msg = f"Deletion error for document ID {file_id}: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return False
