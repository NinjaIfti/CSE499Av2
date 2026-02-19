# API Reference - Backend Endpoints

## Web Routes (HTML Pages)

### Public Routes
- `GET /` - Home page
- `GET /login` - Login page
- `POST /login` - Login form submission
- `GET /register` - Registration page
- `POST /register` - Registration form submission

### Protected Routes (Require Authentication)
- `GET /upload` - Upload video page
- `POST /upload` - Upload video form submission
- `GET /jobs` - List all jobs for current user
- `GET /jobs/<job_id>` - View job status page
- `GET /lectures/<lecture_id>` - View lecture notes page
- `GET /lectures/<lecture_id>/chat` - Chat interface page
- `POST /lectures/<lecture_id>/chat` - Submit chat question (form)
- `GET /logout` - Logout user

## API Endpoints (JSON)

### Job Status API
- `GET /api/jobs/<job_id>/status`
  - Returns: JSON object with job status
  - Response:
    ```json
    {
      "id": 1,
      "user_id": 1,
      "video_path": "storage/job_1/video.mp4",
      "ocr_status": "done",
      "whisper_status": "done",
      "llm_status": "done",
      "final_status": "done",
      "created_at": "2026-02-19T10:00:00",
      "updated_at": "2026-02-19T10:05:00"
    }
    ```

### Chat API
- `POST /api/lectures/<lecture_id>/chat`
  - Request body:
    ```json
    {
      "question": "What is the main topic of this lecture?"
    }
    ```
  - Response:
    ```json
    {
      "answer": "The main topic is..."
    }
    ```
  - Error response:
    ```json
    {
      "error": "Error message"
    }
    ```

## External Service Integration

The backend expects these external services to be available:

### OCR Service
- **URL**: Configured via `OCR_SERVICE_URL`
- **Endpoint**: `POST /process`
- **Request**: 
  - Form data: `video` (file), `job_id` (string)
- **Expected Response**: JSON with OCR results

### Whisper Service
- **URL**: Configured via `WHISPER_SERVICE_URL`
- **Endpoint**: `POST /transcribe`
- **Request**: 
  - Form data: `video` (file), `job_id` (string)
- **Expected Response**: JSON with transcript and timestamps

### LLM Service
- **URL**: Configured via `LLM_SERVICE_URL`
- **Processing Endpoint**: `POST /process`
  - Request body:
    ```json
    {
      "job_id": "1",
      "ocr_output": {...},
      "transcript": {...}
    }
    ```
  - Expected Response: JSON with structured notes, summary
  
- **Chat Endpoint**: `POST /chat`
  - Request body:
    ```json
    {
      "lecture_id": "1",
      "question": "User question",
      "context": {
        "summary": "...",
        "notes": {...},
        "transcript": {...}
      },
      "history": [
        {"question": "...", "answer": "..."}
      ]
    }
    ```
  - Expected Response:
    ```json
    {
      "answer": "Response from LLM"
    }
    ```

## Status Values

- `pending` - Not started
- `running` - Currently processing
- `done` - Completed successfully
- `failed` - Processing failed

## Error Handling

All API endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (missing/invalid parameters)
- `403` - Forbidden (access denied)
- `404` - Not found
- `500` - Internal server error

Error responses include a JSON object with an `error` field:
```json
{
  "error": "Error message description"
}
```
