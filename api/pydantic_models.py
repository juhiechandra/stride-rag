from typing import Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime
from typing import Optional, Annotated


class ModelName(str, Enum):
    # Gemini models
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_PRO = "gemini-2.0-pro"

    # No OpenAI models - removed


class QueryInput(BaseModel):
    session_id: Optional[str] = None
    question: str  # Mandatory field
    model: str = "gemini-2.0-flash"  # Changed from ModelName to str to accept any value

    # Validator to ensure model is a valid Gemini model
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        # If not a Gemini model, default to gemini-2.0-flash
        if not v.startswith("gemini"):
            return "gemini-2.0-flash"
        # If it's already a valid Gemini model, return as is
        if v in [m.value for m in ModelName]:
            return v
        # If it's a Gemini model but not in our enum, default to gemini-2.0-flash
        return "gemini-2.0-flash"

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
    answer: str
    session_id: str
    model: str  # Changed from ModelName to str to match QueryInput

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
    id: int
    filename: str
    upload_timestamp: datetime


class DeleteFileRequest(BaseModel):
    file_id: int
