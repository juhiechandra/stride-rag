import sqlite3
from datetime import datetime
from logger import db_logger, error_logger, PerformanceTimer
import os

DB_NAME = "rag_app.db"

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
        except Exception as e:
            error_msg = f"Failed to create application logs table: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise


def insert_application_logs(session_id, user_query, gpt_response, model):
    with PerformanceTimer(db_logger, f"insert_logs:{session_id}"):
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (?, ?, ?, ?)',
                         (session_id, user_query, gpt_response, model))
            conn.commit()
            conn.close()
            db_logger.info(
                f"Inserted log for session {session_id}, model {model}")
            return True
        except Exception as e:
            error_msg = f"Failed to insert application log: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return False


def get_chat_history(session_id):
    with PerformanceTimer(db_logger, f"get_chat_history:{session_id}"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_query, gpt_response FROM application_logs WHERE session_id = ? ORDER BY created_at', (session_id,))
            messages = []
            for row in cursor.fetchall():
                messages.extend([
                    {"role": "human", "content": row['user_query']},
                    {"role": "ai", "content": row['gpt_response']}
                ])
            conn.close()
            db_logger.info(
                f"Retrieved {len(messages)//2} messages for session {session_id}")
            return messages
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
                db_logger.info(
                    f"Document {filename} already exists with ID {file_id}")
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
    with PerformanceTimer(db_logger, "get_all_documents"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC')
            documents = cursor.fetchall()
            conn.close()
            doc_list = [dict(doc) for doc in documents]
            db_logger.info(f"Retrieved {len(doc_list)} documents")
            return doc_list
        except Exception as e:
            error_msg = f"Failed to retrieve documents: {str(e)}"
            db_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            return []


# Initialize the database tables
try:
    create_application_logs()
    create_document_store()
    db_logger.info("Database tables initialized successfully")
except Exception as e:
    error_msg = f"Failed to initialize database tables: {str(e)}"
    db_logger.error(error_msg)
    error_logger.error(error_msg, exc_info=True)
