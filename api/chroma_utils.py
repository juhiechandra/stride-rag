from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from typing import List, Dict, Tuple
from langchain_core.documents import Document
import fitz  # PyMuPDF
import pdfplumber
import openai
import os
import base64
from datetime import datetime
import traceback
import chromadb


openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the vectorstore
embedding_function = OpenAIEmbeddings()
chroma_client = chromadb.PersistentClient(path="./chroma_db")
vectorstore = Chroma(
    client=chroma_client,
    embedding_function=embedding_function,
    collection_name="document_collection"
)


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

            summary = response['choices'][0]['message']['content']
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


def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    """
    Main function to process PDF and store in vector database
    """
    try:
        print(f"Starting indexing for file_id: {file_id}")
        image_dir = os.path.join("./chroma_db", "extracted_images")

        # Extract data
        texts, images = process_pdf(file_path, image_dir)
        print(f"Extracted {len(texts)} text blocks and {len(images)} images")

        # Improved text splitting strategy
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Smaller chunks for more precise retrieval
            chunk_overlap=200,  # Increased overlap to maintain context
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",",
                        " ", ""],  # More granular separators
            is_separator_regex=False,
        )

        # Add more metadata to improve context
        text_docs = [
            Document(
                page_content=text['content'],
                metadata={
                    'page': text['page'],
                    'file_id': file_id,
                    'type': 'text',
                    'chunk_type': 'document',
                    'timestamp': datetime.now().isoformat(),
                    'source': file_path
                }
            )
            for text in texts
        ]
        text_splits = text_splitter.split_documents(text_docs)

        # Generate image summaries
        image_summaries = get_image_summaries(images)
        for doc in image_summaries:
            doc.metadata['file_id'] = file_id

        # Combine text and image data
        all_documents = text_splits + image_summaries
        if all_documents:
            print(f"Adding {len(all_documents)} documents to vectorstore...")
            vectorstore.add_documents(all_documents)
            print("Documents added successfully")
            return True

        return False
    except Exception as e:
        print(f"Error in document indexing process: {str(e)}")
        return False


def delete_doc_from_chroma(file_id: int):
    try:
        docs = vectorstore.get(where={"file_id": file_id})
        print(
            f"Found {len(docs['ids'])} document chunks for file_id {file_id}")

        vectorstore._collection.delete(where={"file_id": file_id})
        print(f"Deleted all documents with file_id {file_id}")

        return True
    except Exception as e:
        print(
            f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False
