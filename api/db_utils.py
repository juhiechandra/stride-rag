"""
Database Utilities

This module handles all database operations including:
1. Storing and retrieving conversation history
2. Keeping track of uploaded documents
3. Logging system activities and model usage
4. Managing database connections
"""

import sqlite3
from datetime import datetime
from logger import db_logger, error_logger, PerformanceTimer, app_logger
import os

# Name of our database file
DB_NAME = "rag_app.db"

# Check if database exists, create it if needed
db_logger.info(f"Database file: {DB_NAME}")
if not os.path.exists(DB_NAME):
    db_logger.info("Creating new database file")
else:
    db_logger.info(f"Using existing database file: {DB_NAME}")


def get_db_connection():
    """
    Connect to the database.

    This function creates a connection to the SQLite database
    and sets it up to return rows as dictionaries.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # This makes results accessible by column name
        return conn
    except Exception as e:
        error_msg = f"Cannot connect to database: {str(e)}"
        db_logger.error(error_msg)
        error_logger.error(error_msg, exc_info=True)
        raise


def create_application_logs():
    """
    Create the table for storing conversation history.

    This function creates a table that stores:
    - User questions
    - AI responses
    - Which AI model was used
    - When the conversation happened
    """
    with PerformanceTimer(db_logger, "create_conversation_table"):
        try:
            conn = get_db_connection()
            conn.execute('''CREATE TABLE IF NOT EXISTS application_logs
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             session_id TEXT,
                             user_query TEXT,
                             gpt_response TEXT,
                             model TEXT,
                             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            conn.close()
            db_logger.info("Conversation history table ready")
        except Exception as e:
            error_msg = f"Cannot create conversation table: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise


def insert_application_logs(session_id, user_query, gpt_response, model):
    """
    Save a conversation exchange to the database.

    This function stores:
    - The user's question
    - The AI's response
    - Which model generated the response (includes info about whether Gemini was used for RAG)
    - The conversation session ID
    """
    with PerformanceTimer(db_logger, f"save_conversation:{session_id}"):
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (?, ?, ?, ?)',
                         (session_id, user_query, gpt_response, model))
            conn.commit()
            conn.close()
            db_logger.info(f"Saved conversation for session {session_id}")
            app_logger.info(
                f"Saved conversation for session {session_id} using model: {model}")
            return True
        except Exception as e:
            error_msg = f"Cannot save conversation: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            app_logger.error(f"Failed to save conversation: {str(e)}")
            return False


def get_chat_history(session_id):
    """
    Get previous conversation history for a session.

    This function retrieves all previous exchanges between
    the user and AI for a specific conversation session.
    """
    with PerformanceTimer(db_logger, f"get_conversation_history:{session_id}"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_query, gpt_response FROM application_logs WHERE session_id = ? ORDER BY created_at',
                (session_id,)
            )

            # Format the messages for the AI system
            messages = []
            for row in cursor.fetchall():
                messages.extend([
                    {"role": "human", "content": row['user_query']},
                    {"role": "ai", "content": row['gpt_response']}
                ])
            conn.close()

            db_logger.info(
                f"Found {len(messages)//2} previous messages for session {session_id}")
            app_logger.info(
                f"Retrieved {len(messages)//2} previous messages for session {session_id}")
            return messages
        except Exception as e:
            error_msg = f"Cannot retrieve conversation history: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            app_logger.error(
                f"Failed to retrieve conversation history: {str(e)}")
            return []


def create_document_store():
    """
    Create the table for tracking uploaded documents.

    This function creates a table that stores:
    - Document filenames
    - When they were uploaded
    """
    with PerformanceTimer(db_logger, "create_documents_table"):
        try:
            conn = get_db_connection()
            conn.execute('''CREATE TABLE IF NOT EXISTS document_store
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             filename TEXT,
                             upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            conn.close()
            db_logger.info("Documents table ready")
        except Exception as e:
            error_msg = f"Cannot create documents table: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise


def insert_document_record(filename):
    """
    Add a document to the database.

    This function:
    1. Checks if the document already exists
    2. Adds it if it's new
    3. Returns the document's ID
    """
    with PerformanceTimer(db_logger, f"add_document:{filename}"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if this file was already uploaded
            cursor.execute(
                'SELECT id FROM document_store WHERE filename = ?', (filename,))
            existing = cursor.fetchone()

            if existing:
                # Document already exists, return its ID
                file_id = existing['id']
                db_logger.info(
                    f"Document '{filename}' already exists with ID {file_id}")
                app_logger.info(
                    f"Document '{filename}' already exists with ID {file_id}")
                conn.close()
                return file_id

            # Add new document
            cursor.execute(
                'INSERT INTO document_store (filename) VALUES (?)', (filename,))
            file_id = cursor.lastrowid
            conn.commit()
            conn.close()
            db_logger.info(
                f"Added new document: '{filename}' with ID {file_id}")
            app_logger.info(
                f"Added new document: '{filename}' with ID {file_id}")
            return file_id
        except Exception as e:
            error_msg = f"Cannot add document '{filename}': {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            app_logger.error(f"Failed to add document '{filename}': {str(e)}")
            raise


def delete_document_record(file_id):
    """
    Remove a document from the database.

    This function deletes a document's record based on its ID.
    """
    with PerformanceTimer(db_logger, f"remove_document:{file_id}"):
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM document_store WHERE id = ?', (file_id,))
            conn.commit()
            conn.close()
            db_logger.info(f"Removed document with ID {file_id}")
            app_logger.info(f"Removed document with ID {file_id}")
            return True
        except Exception as e:
            error_msg = f"Cannot remove document {file_id}: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            app_logger.error(f"Failed to remove document {file_id}: {str(e)}")
            return False


def get_all_documents():
    """
    Get a list of all uploaded documents.

    This function retrieves information about all documents
    in the system, sorted by upload date (newest first).
    """
    with PerformanceTimer(db_logger, "get_all_documents"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC')
            documents = cursor.fetchall()
            conn.close()

            # Convert database rows to dictionaries
            doc_list = [dict(doc) for doc in documents]
            db_logger.info(f"Found {len(doc_list)} documents")
            app_logger.info(f"Retrieved list of {len(doc_list)} documents")
            return doc_list
        except Exception as e:
            error_msg = f"Cannot retrieve document list: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            app_logger.error(f"Failed to retrieve document list: {str(e)}")
            return []


# Set up the database tables when this module is imported
try:
    create_application_logs()
    create_document_store()
    db_logger.info("Database setup complete")
    app_logger.info("Database tables initialized successfully")
except Exception as e:
    error_msg = f"Database setup failed: {str(e)}"
    db_logger.error(error_msg)
    error_logger.error(error_msg, exc_info=True)
    app_logger.error(f"Database setup failed: {str(e)}")
