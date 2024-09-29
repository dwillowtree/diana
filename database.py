# database.py

import sqlite3
from contextlib import contextmanager
from utils.logging_config import logger
import json

DATABASE_NAME = 'diana.db'

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        logger.info(f"Database connection established: {DATABASE_NAME}")
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

def init_db():
    logger.info("Initializing database")
    try:
        with get_db_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detection_rule TEXT NOT NULL,
                    log_sources TEXT NOT NULL,
                    investigation_steps TEXT NOT NULL,
                    qa_score INTEGER NOT NULL,
                    qa_summary TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS raw_intel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS processed_intel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_intel_id INTEGER,
                    analysis TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (raw_intel_id) REFERENCES raw_intel (id)
                );

                CREATE TABLE IF NOT EXISTS user_inputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    file_content TEXT,
                    model TEXT NOT NULL,
                    data_types TEXT NOT NULL,
                    detection_language TEXT NOT NULL,
                    max_tokens INTEGER NOT NULL,
                    temperature REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS processing_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input_id INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    FOREIGN KEY (user_input_id) REFERENCES user_inputs (id)
                );
            ''')
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise

def get_all_raw_intel():
    logger.info("Retrieving all raw intel")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM raw_intel ORDER BY created_at DESC')
            raw_intel = cursor.fetchall()
            logger.info(f"Retrieved {len(raw_intel)} raw intel entries")
            return [dict(row) for row in raw_intel]
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all raw intel: {e}")
        raise

def get_all_processed_intel():
    logger.info("Retrieving all processed intel")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM processed_intel ORDER BY created_at DESC')
            processed_intel = cursor.fetchall()
            logger.info(f"Retrieved {len(processed_intel)} processed intel entries")
            return [dict(row) for row in processed_intel]
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all processed intel: {e}")
        raise
def store_detection(name, description, detection_rule, log_sources, investigation_steps, qa_score, qa_summary):
    logger.info(f"Storing detection: {name}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO detections (name, description, detection_rule, log_sources, investigation_steps, qa_score, qa_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, detection_rule, log_sources, investigation_steps, qa_score, qa_summary))
            conn.commit()
            detection_id = cursor.lastrowid
            logger.info(f"Detection stored successfully. ID: {detection_id}")
            return detection_id
    except sqlite3.Error as e:
        logger.error(f"Error storing detection: {e}")
        raise
    
def store_user_input(description, file_content, model, data_types, detection_language, max_tokens, temperature):
    logger.info("Storing user input")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_inputs (description, file_content, model, data_types, detection_language, max_tokens, temperature)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (description, file_content, model, json.dumps(data_types), detection_language, max_tokens, temperature))
            conn.commit()
            user_input_id = cursor.lastrowid
            logger.info(f"User input stored successfully. ID: {user_input_id}")
            return user_input_id
    except sqlite3.Error as e:
        logger.error(f"Error storing user input: {e}")
        raise

def store_processing_step(user_input_id, step_name, status, output):
    logger.info(f"Storing processing step: {step_name}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processing_steps (user_input_id, step_name, status, output)
                VALUES (?, ?, ?, ?)
            ''', (user_input_id, step_name, status, output))
            conn.commit()
            step_id = cursor.lastrowid
            logger.info(f"Processing step stored successfully. ID: {step_id}")
            return step_id
    except sqlite3.Error as e:
        logger.error(f"Error storing processing step: {e}")
        raise

def get_detection(detection_id):
    logger.info(f"Attempting to retrieve detection with ID: {detection_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM detections WHERE id = ?', (detection_id,))
            detection = cursor.fetchone()
            if detection:
                logger.info(f"Detection retrieved successfully. ID: {detection_id}")
                return dict(detection)
            else:
                logger.warning(f"No detection found with ID: {detection_id}")
                return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving detection: {e}")
        raise

def get_all_detections():
    logger.info("Attempting to retrieve all detections")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM detections ORDER BY created_at DESC')
            detections = cursor.fetchall()
            logger.info(f"Retrieved {len(detections)} detections")
            return [dict(row) for row in detections]
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all detections: {e}")
        raise

def store_raw_intel(content, source):
    logger.info(f"Attempting to store raw intel from source: {source}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO raw_intel (content, source) VALUES (?, ?)', (content, source))
            conn.commit()
            raw_intel_id = cursor.lastrowid
            logger.info(f"Raw intel stored successfully. ID: {raw_intel_id}")
            return raw_intel_id
    except sqlite3.Error as e:
        logger.error(f"Error storing raw intel: {e}")
        raise

def store_processed_intel(raw_intel_id, analysis):
    logger.info(f"Attempting to store processed intel for raw intel ID: {raw_intel_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO processed_intel (raw_intel_id, analysis) VALUES (?, ?)', (raw_intel_id, analysis))
            conn.commit()
            processed_intel_id = cursor.lastrowid
            logger.info(f"Processed intel stored successfully. ID: {processed_intel_id}")
            return processed_intel_id
    except sqlite3.Error as e:
        logger.error(f"Error storing processed intel: {e}")
        raise

def get_all_raw_intel():
    logger.info("Attempting to retrieve all raw intel")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM raw_intel ORDER BY created_at DESC')
            raw_intel = cursor.fetchall()
            logger.info(f"Retrieved {len(raw_intel)} raw intel entries")
            return [dict(row) for row in raw_intel]
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all raw intel: {e}")
        raise

def get_all_processed_intel():
    logger.info("Attempting to retrieve all processed intel")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pi.*, ri.source
                FROM processed_intel pi
                JOIN raw_intel ri ON pi.raw_intel_id = ri.id
                ORDER BY pi.created_at DESC
            ''')
            processed_intel = cursor.fetchall()
            logger.info(f"Retrieved {len(processed_intel)} processed intel entries")
            return [dict(row) for row in processed_intel]
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all processed intel: {e}")
        raise

# Initialize the database when this module is imported
try:
    init_db()
except Exception as e:
    logger.critical(f"Failed to initialize database: {e}")
    raise