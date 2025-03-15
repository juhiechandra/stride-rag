"""
Data Models for the API

This module defines the data structures used in the API:
1. Available AI models
2. Input formats for questions
3. Output formats for answers
4. Document information
5. File deletion requests

Note: Gemini models are used for RAG operations.
"""

from typing import Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class ModelName(str, Enum):
    """
    Available AI models that can be used to answer questions.

    This enum defines the supported AI models from Google.
    """
    # Google Gemini models for RAG operations
    GEMINI_2_0_FLASH = "gemini-2.0-flash"  # Faster, good for most questions
    # More powerful, better for complex questions
    GEMINI_2_0_PRO = "gemini-2.0-pro"


class QueryInput(BaseModel):
    """
    Input format for asking questions.

    This model defines what information is needed when a user
    asks a question about documents.

    Note: If a non-Gemini model is selected, the system will automatically
    use Gemini for RAG operations while preserving the original model choice
    in the response.
    """
    session_id: Optional[str] = None  # Optional ID to track conversation history
    question: str                     # The user's question (required)
    # Which AI model to use (default: Gemini Flash)
    model: ModelName = ModelName.GEMINI_2_0_FLASH

    # Example for API documentation
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "some-uuid-here",
                    "question": "What is RAG?",
                    "model": "gemini-2.0-flash"
                }
            ]
        }
    }


class QueryResponse(BaseModel):
    """
    Output format for question answers.

    This model defines what information is returned when
    the system answers a question.

    Note: Even if a non-Gemini model was requested, the actual processing
    will use Gemini for RAG operations. The original model choice is preserved
    in this response.
    """
    answer: str         # The AI's answer to the question
    session_id: str     # ID to track conversation history
    model: ModelName    # The originally requested AI model

    # Example for API documentation
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "RAG stands for Retrieval Augmented Generation...",
                    "session_id": "some-uuid-here",
                    "model": "gemini-2.0-flash"
                }
            ]
        }
    }


class DocumentInfo(BaseModel):
    """
    Information about an uploaded document.

    This model defines what information is stored and
    returned about each document in the system.
    """
    id: int                 # Unique identifier for the document
    filename: str           # Name of the document file
    upload_timestamp: datetime  # When the document was uploaded


class DeleteFileRequest(BaseModel):
    """
    Request to delete a document.

    This model defines what information is needed to
    delete a document from the system.
    """
    file_id: int  # ID of the document to delete
