from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
import pdfplumber
import openai
import os
import chromadb
from datetime import datetime
import base64
from PIL import Image
import traceback

# Set up OpenAI API key
os.environ["OPENAI_API_KEY"] = "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"
openai.api_key = os.getenv("OPENAI_API_KEY")


def extract_images_pymupdf(pdf_path: str, output_dir: str) -> List[Dict]:
    """
    Extract images from a PDF using PyMuPDF.

    Args:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Directory to save the extracted images.

    Returns:
        List[Dict]: A list of dictionaries containing image metadata and base64 encoding.
    """
    print("Extracting images with PyMuPDF...")
    images = []
    os.makedirs(output_dir, exist_ok=True)

    try:
        pdf_document = fitz.open(pdf_path)

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            image_list = page.get_images()
            print(f"Found {len(image_list)} images on page {page_num + 1}")

            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Convert to base64
                    image_base64 = base64.b64encode(
                        image_bytes).decode('utf-8')

                    # Save image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_filename = f"page{page_num + 1}_img{img_index + 1}.{base_image['ext']}"
                    image_path = os.path.join(output_dir, image_filename)

                    with open(image_path, "wb") as image_file:
                        image_file.write(image_bytes)

                    images.append({
                        'page': page_num + 1,
                        'file_path': image_path,
                        'base64': image_base64
                    })
                    print(f"Saved image: {image_path}")
                except Exception as e:
                    print(
                        f"Error extracting image {img_index} from page {page_num + 1}: {e}")

        pdf_document.close()

    except Exception as e:
        print(f"PyMuPDF extraction error: {e}")

    return images


def extract_text_pdfplumber(pdf_path: str) -> List[Dict]:
    """
    Extract text from a PDF using pdfplumber.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        List[Dict]: A list of dictionaries containing extracted text and page numbers.
    """
    print("Extracting text with pdfplumber...")
    texts = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    texts.append({'content': text, 'page': page_num + 1})
    except Exception as e:
        print(f"pdfplumber text extraction error: {e}")

    return texts


def get_image_summaries(images: List[Dict]) -> List[Document]:
    """
    Generate image summaries using OpenAI ChatCompletion API.

    Args:
        images (List[Dict]): List of image metadata and base64 strings.

    Returns:
        List[Document]: A list of LangChain Document objects containing image summaries.
    """
    summaries = []
    for image in images:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Describe the given image in detail."},
                    {"role": "user",
                        "content": f"data:image/jpeg;base64,{image['base64']}"}
                ],
                max_tokens=300
            )

            summary = response.choices[0].message['content']
            summaries.append(Document(
                page_content=summary,
                metadata={
                    'type': 'image',
                    'page': image['page'],
                    'file_path': image['file_path']
                }
            ))
            print(f"Generated summary for image on page {image['page']}")

        except Exception as e:
            print(
                f"Error generating image summary for page {image['page']}: {e}")
            print(f"Full traceback: {traceback.format_exc()}")

    return summaries


def process_pdf(pdf_path: str, output_dir: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a PDF to extract text and images.

    Args:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Directory to save extracted images.

    Returns:
        Tuple[List[Dict], List[Dict]]: Extracted text and image data.
    """
    os.makedirs(output_dir, exist_ok=True)

    texts = extract_text_pdfplumber(pdf_path)
    images = extract_images_pymupdf(pdf_path, output_dir)

    return texts, images


def index_document_to_chroma(file_path: str, vectorstore: Chroma, file_id: str) -> bool:
    """
    Index extracted text and image summaries into a Chroma vectorstore.

    Args:
        file_path (str): Path to the input PDF file.
        vectorstore (Chroma): Chroma vectorstore object.
        file_id (str): Unique identifier for the file.

    Returns:
        bool: True if indexing was successful, False otherwise.
    """
    try:
        print(f"Starting indexing for file_id: {file_id}")

        # Directory to store extracted images
        base_dir = "/Users/juhiechandra/Downloads/0rag-module-backend-main/test_db"
        image_dir = os.path.join(base_dir, "extracted_images")

        # Extract data
        texts, images = process_pdf(file_path, image_dir)
        print(f"Extracted {len(texts)} text blocks and {len(images)} images")

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100)
        text_docs = [
            Document(page_content=text['content'], metadata={
                     'page': text['page'], 'file_id': file_id, 'type': 'text'})
            for text in texts
        ]
        text_splits = text_splitter.split_documents(text_docs)

        # Generate image summaries
        image_summaries = get_image_summaries(images)

        # Combine text and image data
        all_documents = text_splits + image_summaries
        if all_documents:
            vectorstore.add_documents(all_documents)
            print(f"Added {len(all_documents)} documents to vectorstore")
            return True

        return False
    except Exception as e:
        print(f"Error indexing document: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    # Initialize vectorstore
    embedding_function = OpenAIEmbeddings()
    chroma_client = chromadb.PersistentClient(
        path="/Users/juhiechandra/Downloads/0rag-module-backend-main/test_db")
    vectorstore = Chroma(
        client=chroma_client,
        embedding_function=embedding_function,
        collection_name="document_collection"
    )

    # File details
    file_path = "/Users/juhiechandra/Downloads/0rag-module-backend-main/doc.pdf"
    file_id = "unique_file_id"

    # Process and index the document
    success = index_document_to_chroma(file_path, vectorstore, file_id)
    if success:
        print("Document successfully processed and indexed.")
    else:
        print("Failed to process document.")
