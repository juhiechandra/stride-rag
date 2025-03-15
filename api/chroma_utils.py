"""
Document Processing and Storage Utilities

This module handles:
1. Extracting text from PDF documents
2. Extracting images from PDF documents
3. Generating descriptions for images using OpenAI (GPT-4o-mini only)
4. Storing document content for searching using Gemini embeddings
5. Deleting documents from storage

Note: OpenAI is ONLY used for image descriptions, while Gemini is used for all embeddings.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Dict
from langchain_core.documents import Document
import fitz  # PyMuPDF
import pdfplumber
import google.generativeai as genai
from openai import OpenAI
import os
import base64
import chromadb
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from logger import model_logger, error_logger, PerformanceTimer, log_token_usage, app_logger

# Load API keys from .env file
load_dotenv()

# Set up AI services
app_logger.info("Setting up AI services")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# OpenAI client - ONLY used for image descriptions
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app_logger.info(
    "AI services configured: Gemini for embeddings, OpenAI for image descriptions only")

# Set up the database for storing document content
chroma_db_path = "./chroma_db"
os.makedirs(chroma_db_path, exist_ok=True)
app_logger.info(f"Database path: {chroma_db_path}")

try:
    # Connect to the database
    chroma_client = chromadb.PersistentClient(
        path=chroma_db_path,
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True
        )
    )
    app_logger.info("Database connected")
except Exception as e:
    error_logger.error(
        f"Failed to connect to database: {str(e)}", exc_info=True)
    raise

try:
    # Set up the system that converts text to searchable format - USING GEMINI ONLY
    embedding_function = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        task_type="retrieval_document"
    )
    app_logger.info("Gemini embedding system ready")
    log_token_usage("gemini-embedding-001", "embedding_setup", 0, 0, 0)
except Exception as e:
    error_logger.error(
        f"Failed to set up Gemini embeddings: {str(e)}", exc_info=True)
    app_logger.error(f"Failed to set up Gemini embeddings: {str(e)}")
    raise

try:
    # Create the storage system for document content
    vectorstore = Chroma(
        client=chroma_client,
        embedding_function=embedding_function,
        collection_name="document_collection"
    )
    app_logger.info("Document storage system ready")
except Exception as e:
    error_logger.error(
        f"Failed to set up document storage: {str(e)}", exc_info=True)
    raise


def extract_images_pymupdf(pdf_path: str, output_dir: str) -> List[Dict]:
    """
    Extract all images from a PDF file.

    This function:
    1. Opens a PDF file
    2. Finds all images on each page
    3. Saves each image to a file
    4. Returns information about all found images
    """
    with PerformanceTimer(app_logger, f"extract_images:{os.path.basename(pdf_path)}"):
        images = []
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Open the PDF file
            pdf_document = fitz.open(pdf_path)
            app_logger.info(
                f"PDF opened: {pdf_path} ({len(pdf_document)} pages)")

            # Process each page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                image_list = page.get_images()
                app_logger.info(
                    f"Found {len(image_list)} images on page {page_num+1}")

                # Process each image on the page
                for img_index, img in enumerate(image_list):
                    try:
                        # Extract the image data
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]

                        # Convert to base64 and save to file
                        image_base64 = base64.b64encode(
                            image_bytes).decode('utf-8')
                        image_filename = f"page{page_num+1}_img{img_index+1}.{base_image['ext']}"
                        image_path = os.path.join(output_dir, image_filename)

                        with open(image_path, "wb") as f:
                            f.write(image_bytes)

                        # Store image information
                        images.append({
                            'page': page_num + 1,
                            'file_path': image_path,
                            'base64': image_base64
                        })
                        app_logger.info(
                            f"Saved image: {image_filename} ({len(image_bytes)} bytes)")
                    except Exception as e:
                        error_msg = f"Error with image {img_index} on page {page_num+1}: {str(e)}"
                        model_logger.error(error_msg)
                        error_logger.error(error_msg, exc_info=True)

            pdf_document.close()
            app_logger.info(f"Found {len(images)} total images in {pdf_path}")
        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)

        return images


def extract_text_pdfplumber(pdf_path: str) -> List[Dict]:
    """
    Extract all text from a PDF file.

    This function:
    1. Opens a PDF file
    2. Extracts text from each page
    3. Returns the text content with page numbers
    """
    with PerformanceTimer(app_logger, f"extract_text:{os.path.basename(pdf_path)}"):
        texts = []

        try:
            # Open the PDF file
            with pdfplumber.open(pdf_path) as pdf:
                app_logger.info(
                    f"PDF opened: {pdf_path} ({len(pdf.pages)} pages)")

                # Process each page
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        # Store text with page number
                        texts.append({'content': text, 'page': page_num + 1})
                        char_count = len(text)
                        app_logger.info(
                            f"Found {char_count} characters on page {page_num+1}")
                    else:
                        app_logger.info(f"No text found on page {page_num+1}")

                app_logger.info(f"Found text on {len(texts)} pages total")
        except Exception as e:
            error_msg = f"Error extracting text: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)

        return texts


def get_image_summaries(images: List[Dict]) -> List[Document]:
    """
    Generate descriptions for images using OpenAI GPT-4o-mini.

    This function:
    1. Takes a list of images
    2. Sends each image to OpenAI GPT-4o-mini model (ONLY for image description)
    3. Gets a text description of each image
    4. Returns the descriptions with metadata

    Note: OpenAI is ONLY used here for image-to-text conversion
    """
    with PerformanceTimer(app_logger, f"describe_images:{len(images)} images"):
        summaries = []
        MAX_IMAGES = 10  # Limit to avoid processing too many images

        app_logger.info(
            f"Describing {min(len(images), MAX_IMAGES)} images using OpenAI GPT-4o-mini")

        for i, image in enumerate(images[:MAX_IMAGES]):
            with PerformanceTimer(app_logger, f"describe_image:{i+1}"):
                try:
                    # Load the image
                    img_bytes = base64.b64decode(image['base64'])
                    img = Image.open(BytesIO(img_bytes))
                    app_logger.info(f"Processing image {i+1}: size {img.size}")

                    # Make the image smaller to save processing time and tokens
                    img.thumbnail((800, 800))
                    buffer = BytesIO()
                    img.save(buffer, format="JPEG", quality=85)
                    processed_base64 = base64.b64encode(
                        buffer.getvalue()).decode('utf-8')
                    app_logger.info(
                        f"Image {i+1} resized to {img.size}, compressed from {len(img_bytes)} to {len(buffer.getvalue())} bytes")

                    # Ask OpenAI GPT-4o-mini to describe the image (ONLY use case for OpenAI)
                    app_logger.info(
                        f"Getting description for image {i+1} using OpenAI GPT-4o-mini")
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",  # Using the smaller model to save costs
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Describe this image in detail for document retrieval:"},
                                {"type": "image_url", "image_url": {
                                    "url": f"data:image/jpeg;base64,{processed_base64}"}}
                            ]
                        }],
                        max_tokens=300
                    )

                    # Get the description
                    summary = response.choices[0].message.content

                    # Log token usage for OpenAI
                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    total_tokens = response.usage.total_tokens
                    log_token_usage("gpt-4o-mini", "image_description",
                                    input_tokens, output_tokens, total_tokens)

                    app_logger.info(
                        f"Got description for image {i+1}: {len(summary)} characters, used {total_tokens} tokens")

                    # Store the description with metadata
                    summaries.append(Document(
                        page_content=summary,
                        metadata={
                            'type': 'image',
                            'page': image['page'],
                            'file_path': image['file_path']
                        }
                    ))
                except Exception as e:
                    error_msg = f"Error describing image {i+1}: {str(e)}"
                    model_logger.error(error_msg)
                    error_logger.error(error_msg, exc_info=True)

        app_logger.info(
            f"Created {len(summaries)} image descriptions total using OpenAI GPT-4o-mini")
        return summaries


def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    """
    Process a document and store its content for searching.

    This function:
    1. Extracts text from the document
    2. Extracts images from the document
    3. Gets descriptions for the images using OpenAI GPT-4o-mini ONLY
    4. Splits text into searchable chunks
    5. Stores everything in the database using Gemini embeddings ONLY
    """
    with PerformanceTimer(app_logger, f"process_document:{os.path.basename(file_path)}"):
        try:
            # Create folder for extracted images
            image_dir = os.path.join(chroma_db_path, "extracted_images")
            os.makedirs(image_dir, exist_ok=True)
            app_logger.info(
                f"Starting to process document: {file_path} (ID: {file_id})")

            # Get text and images from the document
            app_logger.info(f"Extracting text from {file_path}")
            texts = extract_text_pdfplumber(file_path)
            app_logger.info(f"Extracting images from {file_path}")
            images = extract_images_pymupdf(file_path, image_dir)

            # Process the text
            app_logger.info(f"Processing {len(texts)} text sections")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " "]
            )

            # Create document objects for each text section
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

            # Split text into smaller chunks for better searching
            text_chunks = text_splitter.split_documents(text_docs)
            app_logger.info(
                f"Split text into {len(text_chunks)} searchable chunks")

            # Process the images using OpenAI GPT-4o-mini for descriptions
            app_logger.info(
                f"Processing {len(images)} images with OpenAI GPT-4o-mini")
            image_summaries = get_image_summaries(images)
            for doc in image_summaries:
                doc.metadata.update({'file_id': file_id})
            app_logger.info(
                f"Created {len(image_summaries)} image descriptions with OpenAI GPT-4o-mini")

            # Combine text and image content and store in database using Gemini embeddings
            all_docs = text_chunks + image_summaries
            app_logger.info(
                f"Storing {len(all_docs)} total items in database using Gemini embeddings")

            if all_docs:
                # This uses Gemini embeddings as configured earlier
                vectorstore.add_documents(all_docs)
                # Estimate token usage for embeddings (rough estimate)
                total_text = sum(len(doc.page_content) for doc in all_docs)
                estimated_tokens = total_text // 4  # Rough estimate: 4 chars per token
                log_token_usage("gemini-embedding-001", "document_embedding",
                                estimated_tokens, 0, estimated_tokens)

                app_logger.info(
                    f"Successfully processed document {file_path} (ID: {file_id})")
                return True

            app_logger.warning(f"No content found in document {file_path}")
            return False

        except Exception as e:
            error_msg = f"Error processing document {file_path}: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return False


def delete_doc_from_chroma(file_id: int) -> bool:
    """
    Delete a document from the database.

    This function removes all content associated with a document ID
    from the search database.
    """
    with PerformanceTimer(app_logger, f"delete_document:{file_id}"):
        try:
            app_logger.info(f"Deleting document ID {file_id} from database")
            vectorstore._collection.delete(where={"file_id": file_id})
            app_logger.info(f"Successfully deleted document ID {file_id}")
            return True
        except Exception as e:
            error_msg = f"Error deleting document ID {file_id}: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return False
