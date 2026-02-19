import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///lecture_intelligence.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # External service URLs (ngrok endpoints)
    OCR_SERVICE_URL = os.environ.get('OCR_SERVICE_URL') or 'http://localhost:5001'
    WHISPER_SERVICE_URL = os.environ.get('WHISPER_SERVICE_URL') or 'http://localhost:5002'
    LLM_SERVICE_URL = os.environ.get('LLM_SERVICE_URL') or 'http://localhost:5003'
    
    # Service timeout settings (in seconds)
    SERVICE_TIMEOUT = int(os.environ.get('SERVICE_TIMEOUT', '300'))
    POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '5'))
    MAX_POLL_ATTEMPTS = int(os.environ.get('MAX_POLL_ATTEMPTS', '120'))
    
    # File upload settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'storage'
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    # Chat settings
    CHAT_TIMEOUT = int(os.environ.get('CHAT_TIMEOUT', '60'))
