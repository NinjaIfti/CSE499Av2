# LLM Service Connection Guide

## Current Status

Your teammate's notebook (`llmpart.ipynb`) has:
- ✅ FastAPI setup
- ✅ Model loading (Long-T5)
- ✅ ngrok tunnel
- ❌ **Missing**: `/process` endpoint (needed for merging OCR + transcript)
- ❌ **Missing**: `/chat` endpoint (needed for Q&A)

## What Needs to Be Fixed

The backend expects these endpoints:

### 1. `/process` Endpoint
**Purpose**: Merge OCR + transcript and generate structured notes

**Expected Request**:
```json
{
  "job_id": "1",
  "ocr_output": {...},
  "transcript": {...}
}
```

**Expected Response**:
```json
{
  "summary": "Generated summary text",
  "key_points": ["point1", "point2", ...],
  "notes": {
    "ocr_content": {...},
    "transcript_content": {...},
    "merged_text": "..."
  }
}
```

### 2. `/chat` Endpoint
**Purpose**: Answer questions about lectures

**Expected Request**:
```json
{
  "lecture_id": "1",
  "question": "What is the main topic?",
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

**Expected Response**:
```json
{
  "answer": "Response text"
}
```

## Solution

I've created `llmpart_updated.ipynb` with:
- ✅ `/process` endpoint that merges OCR + transcript
- ✅ `/chat` endpoint for Q&A
- ✅ Proper error handling
- ✅ Matches backend API contract

## How to Connect

### Step 1: Update the Notebook
Share `llmpart_updated.ipynb` with your teammate OR have them add these endpoints to their existing notebook.

### Step 2: Run the Updated Notebook
When they run it, they'll get an ngrok URL like:
```
https://xxxxx.ngrok-free.dev
```

### Step 3: Update Your `.env` File
Add the ngrok URL to your Flask backend:

```env
LLM_SERVICE_URL=https://xxxxx.ngrok-free.dev
```

### Step 4: Test Connection
Restart your Flask app and try uploading a video. The backend will call:
- `POST {LLM_SERVICE_URL}/process` when OCR + Whisper complete
- `POST {LLM_SERVICE_URL}/chat` when users ask questions

## Quick Fix for Current Notebook

If you want to quickly test with the current notebook, you can temporarily modify your backend's `services/orchestrator.py` to call `/summarize` instead, but this is **not recommended** for production. The proper solution is to add the `/process` and `/chat` endpoints.

## Testing the LLM Service

Once updated, test with:

```python
import requests

# Test /process
response = requests.post(
    "https://your-ngrok-url.ngrok-free.dev/process",
    json={
        "job_id": "1",
        "ocr_output": {"text": "Sample OCR text"},
        "transcript": {"text": "Sample transcript"}
    }
)
print(response.json())

# Test /chat
response = requests.post(
    "https://your-ngrok-url.ngrok-free.dev/chat",
    json={
        "lecture_id": "1",
        "question": "What is this about?",
        "context": {
            "summary": "Test summary",
            "notes": {},
            "transcript": {}
        },
        "history": []
    }
)
print(response.json())
```
