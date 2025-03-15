from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, Annotated


class ModelName(str, Enum):
    # Gemini models
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_PRO = "gemini-2.0-pro"

    # OpenAI models
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


class QueryInput(BaseModel):
    session_id: Optional[str] = None
    question: str  # Mandatory field
    model: ModelName = ModelName.GEMINI_2_0_FLASH  # Default value

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
    model: ModelName

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
