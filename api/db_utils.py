import sqlite3
from datetime import datetime
from logger import db_logger, error_logger, PerformanceTimer
import os

DB_NAME = "rag_app.db"
UPLOAD_DIR = "./uploaded_files"

# Initialize database
db_logger.info(f"Database path: {DB_NAME}")
if not os.path.exists(DB_NAME):
    db_logger.info("Creating new database")
else:
    db_logger.info(f"Using existing database: {DB_NAME}")


def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        error_msg = f"Failed to connect to database: {str(e)}"
        db_logger.error(error_msg)
        error_logger.error(error_msg, exc_info=True)
        raise


def check_column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()

        for column in columns:
            if column['name'] == column_name:
                return True
        return False
    except Exception as e:
        error_msg = f"Failed to check column existence: {str(e)}"
        db_logger.error(error_msg)
        error_logger.error(error_msg, exc_info=True)
        return False


def add_column_if_not_exists(table_name, column_name, column_type):
    """Add a column to a table if it doesn't exist."""
    try:
        if not check_column_exists(table_name, column_name):
            conn = get_db_connection()
            conn.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            conn.commit()
            conn.close()
            db_logger.info(f"Added column {column_name} to table {table_name}")
            return True
        return False
    except Exception as e:
        error_msg = f"Failed to add column {column_name} to table {table_name}: {str(e)}"
        db_logger.error(error_msg)
        error_logger.error(error_msg, exc_info=True)
        return False


def create_application_logs():
    with PerformanceTimer(db_logger, "create_application_logs"):
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
            db_logger.info("Application logs table created or verified")

            # Add processing_time column if it doesn't exist
            add_column_if_not_exists(
                "application_logs", "processing_time", "REAL")

        except Exception as e:
            error_msg = f"Failed to create application logs table: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise


def insert_application_logs(session_id, question, answer, model, processing_time=0.0):
    with PerformanceTimer(db_logger, f"insert_logs:{session_id}"):
        try:
            # Ensure the processing_time column exists
            add_column_if_not_exists(
                "application_logs", "processing_time", "REAL")

            conn = get_db_connection()
            conn.execute('''INSERT INTO application_logs 
                            (session_id, user_query, gpt_response, model, processing_time) 
                            VALUES (?, ?, ?, ?, ?)''',
                         (session_id, question, answer, model, processing_time))
            conn.commit()
            conn.close()
            db_logger.info(f"Inserted log for session: {session_id}")
        except Exception as e:
            error_msg = f"Failed to insert application log: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise


def get_chat_history(session_id):
    with PerformanceTimer(db_logger, f"get_chat_history:{session_id}"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_query, gpt_response FROM application_logs WHERE session_id = ? ORDER BY created_at', (session_id,))
            history = []
            for row in cursor.fetchall():
                history.append({
                    "question": row['user_query'],
                    "answer": row['gpt_response']
                })
            conn.close()
            db_logger.info(
                f"Retrieved {len(history)} messages for session {session_id}")
            return history
        except Exception as e:
            error_msg = f"Failed to retrieve chat history for session {session_id}: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return []


def create_document_store():
    with PerformanceTimer(db_logger, "create_document_store"):
        try:
            conn = get_db_connection()
            conn.execute('''CREATE TABLE IF NOT EXISTS document_store
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             filename TEXT,
                             upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            conn.close()
            db_logger.info("Document store table created or verified")
        except Exception as e:
            error_msg = f"Failed to create document store table: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise


def insert_document_record(filename):
    with PerformanceTimer(db_logger, f"insert_document:{filename}"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if file already exists
            cursor.execute(
                'SELECT id FROM document_store WHERE filename = ?', (filename,))
            existing = cursor.fetchone()

            if existing:
                file_id = existing['id']
                # Update the timestamp to current time
                cursor.execute(
                    'UPDATE document_store SET upload_timestamp = CURRENT_TIMESTAMP WHERE id = ?', (file_id,))
                conn.commit()
                db_logger.info(
                    f"Document {filename} already exists with ID {file_id}, updated timestamp")
                conn.close()
                return file_id

            # If not exists, insert new record
            cursor.execute(
                'INSERT INTO document_store (filename) VALUES (?)', (filename,))
            file_id = cursor.lastrowid
            conn.commit()
            conn.close()
            db_logger.info(
                f"Inserted new document record: {filename} with ID {file_id}")
            return file_id
        except Exception as e:
            error_msg = f"Failed to insert document record for {filename}: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise


def delete_document_record(file_id):
    with PerformanceTimer(db_logger, f"delete_document:{file_id}"):
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM document_store WHERE id = ?', (file_id,))
            conn.commit()
            conn.close()
            db_logger.info(f"Deleted document record with ID {file_id}")
            return True
        except Exception as e:
            error_msg = f"Failed to delete document record {file_id}: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return False


def get_all_documents():
    """Get all documents from the database."""
    with PerformanceTimer(db_logger, "get_all_documents"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC")
            documents = cursor.fetchall()
            conn.close()

            result = []
            for doc in documents:
                result.append({
                    "id": doc["id"],
                    "filename": doc["filename"],
                    "upload_timestamp": doc["upload_timestamp"]
                })
            return result
        except Exception as e:
            error_msg = f"Failed to get documents: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return []


def get_document_path(file_id):
    """Get the path of a document by its ID."""
    with PerformanceTimer(db_logger, f"get_document_path:{file_id}"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filename FROM document_store WHERE id = ?", (file_id,))
            document = cursor.fetchone()
            conn.close()

            if document:
                # First check if the file exists in the upload directory
                filename = document["filename"]
                upload_path = os.path.join(
                    UPLOAD_DIR, f"doc-{file_id}-{filename}")

                if os.path.exists(upload_path):
                    db_logger.info(
                        f"Found document in upload directory: {upload_path}")
                    return upload_path

                # Fall back to the old location if not found in upload directory
                old_path = os.path.join(
                    "./faiss_db/document_collection", filename)
                if os.path.exists(old_path):
                    db_logger.info(
                        f"Found document in old location: {old_path}")
                    return old_path

                db_logger.error(f"Document file not found for ID {file_id}")
                return None
            return None
        except Exception as e:
            error_msg = f"Failed to get document path: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return None


# Initialize the database tables
try:
    create_application_logs()
    create_document_store()
    db_logger.info("Database tables initialized successfully")
except Exception as e:
    error_msg = f"Failed to initialize database tables: {str(e)}"
    db_logger.error(error_msg)
    error_logger.error(error_msg, exc_info=True)
