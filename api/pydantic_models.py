from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime
from typing import Optional, Annotated


class ModelName(str, Enum):
    # Gemini models
    GEMINI_2_5_FLASH = "gemini-2.5-flash"


class QueryInput(BaseModel):
    session_id: Optional[str] = None
    question: str  # Mandatory field
    model: str = "gemini-2.5-flash"  # Default to gemini-2.5-flash

    # Validator to ensure model is a valid Gemini model
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        # If not a Gemini model, default to gemini-2.5-flash
        if not v.startswith("gemini"):
            return "gemini-2.5-flash"
        # If it's already a valid Gemini model, return as is
        if v in [m.value for m in ModelName]:
            return v
        # If it's a Gemini model but not in our enum, default to gemini-2.5-flash
        return "gemini-2.5-flash"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "some-uuid-here",
                    "question": "What is RAG?",
                    "model": "gemini-2.5-flash"
                }
            ]
        }
    }


class QueryResponse(BaseModel):
    answer: str
    processing_time: float
    model: str  # Changed from ModelName to str to match QueryInput

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "RAG stands for Retrieval Augmented Generation...",
                    "processing_time": 1.25,
                    "model": "gemini-2.5-flash"
                }
            ]
        }
    }


class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime


class DeleteFileRequest(BaseModel):
    file_id: int
