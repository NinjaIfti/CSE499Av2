# Setup Guide - Lecture AI

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd s:\GitHub\CSE499Av2
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Update the service URLs with your ngrok endpoints:
     ```
     OCR_SERVICE_URL=http://your-ocr-ngrok-url
     WHISPER_SERVICE_URL=http://your-whisper-ngrok-url
     LLM_SERVICE_URL=http://your-llm-ngrok-url
     ```
   - Change `SECRET_KEY` to a secure random string for production

6. **Initialize the database**
   - The database will be created automatically on first run
   - A default admin user will be created:
     - Email: `admin@example.com`
     - Password: `admin123`

## Running the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Project Structure

```
CSE499Av2/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models (SQLAlchemy)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── services/
│   ├── __init__.py
│   ├── orchestrator.py   # Orchestration logic for external services
│   └── chat_service.py   # Chat service for LLM interactions
├── templates/            # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── jobs.html
│   ├── job_status.html
│   ├── lecture_view.html
│   ├── chat.html
│   ├── 404.html
│   └── 500.html
├── static/
│   └── css/
│       └── style.css     # Stylesheet
└── storage/              # File storage (created automatically)
    └── job_<id>/         # Per-job storage directories
        ├── video.mp4
        ├── ocr_output.json
        ├── transcript.json
        └── final_notes.json
```

## External Service API Contracts

### OCR Service
- **Endpoint**: `POST /process`
- **Request**: 
  - Form data with `video` file and `job_id`
- **Response**: JSON with OCR results

### Whisper Service
- **Endpoint**: `POST /transcribe`
- **Request**: 
  - Form data with `video` file and `job_id`
- **Response**: JSON with transcript and timestamps

### LLM Service
- **Endpoint**: `POST /process`
- **Request**: 
  - JSON with `job_id`, `ocr_output`, `transcript`
- **Response**: JSON with structured notes, summary

- **Chat Endpoint**: `POST /chat`
- **Request**: 
  - JSON with `lecture_id`, `question`, `context`, `history`
- **Response**: JSON with `answer`

## Usage Workflow

1. **Register/Login**: Create an account or login
2. **Upload Video**: Upload a lecture video file
3. **Monitor Progress**: View job status page (auto-refreshes)
4. **View Lecture**: Once processing completes, view structured notes
5. **Chat**: Ask questions about the lecture content

## Database Schema

- **Users**: User accounts and authentication
- **Jobs**: Processing jobs with status tracking
- **Lectures**: Processed lecture data (notes, transcripts)
- **Chats**: Chat conversation history

## Configuration Options

All configuration is in `config.py` and can be overridden via environment variables:

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: SQLite database path
- `OCR_SERVICE_URL`: OCR service ngrok URL
- `WHISPER_SERVICE_URL`: Whisper service ngrok URL
- `LLM_SERVICE_URL`: LLM service ngrok URL
- `SERVICE_TIMEOUT`: HTTP request timeout (seconds)
- `POLL_INTERVAL`: Status polling interval (seconds)
- `MAX_POLL_ATTEMPTS`: Maximum polling attempts
- `UPLOAD_FOLDER`: Storage directory path
- `MAX_CONTENT_LENGTH`: Maximum file upload size (bytes)

## Troubleshooting

1. **Database errors**: Delete `lecture_intelligence.db` and restart to recreate
2. **Service connection errors**: Verify ngrok URLs are correct and services are running
3. **File upload errors**: Check file size limits and storage directory permissions
4. **Import errors**: Ensure virtual environment is activated and dependencies are installed

## Production Deployment Notes

- Change `SECRET_KEY` to a secure random value
- Use a production WSGI server (e.g., Gunicorn, uWSGI)
- Set up proper database backups
- Configure reverse proxy (nginx)
- Use environment variables for all sensitive configuration
- Enable HTTPS
- Set up monitoring and logging
