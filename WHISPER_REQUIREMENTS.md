# Whisper Service Requirements

## Overview
The Whisper service performs speech-to-text transcription on lecture videos. This service extracts audio from video and generates a transcript with timestamps. It runs in parallel with the OCR service.

---

## API Endpoint Specification

### Endpoint Details
- **URL Path**: `/transcribe`
- **HTTP Method**: `POST`
- **Content-Type**: `multipart/form-data`

### Request Format

**Form Fields:**
- `video` (file, required) - Video file to transcribe
  - Supported formats: MP4, AVI, MOV, MKV, WebM
  - Maximum size: 500MB (handled by backend)
- `job_id` (string, required) - Job identifier from backend

**Example Request:**
```python
import requests

files = {'video': open('lecture.mp4', 'rb')}
data = {'job_id': '123'}
response = requests.post('https://your-ngrok-url/transcribe', files=files, data=data)
```

### Response Format

**Success Response (HTTP 200):**
```json
{
  "text": "Full transcript of the entire lecture",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Welcome to today's lecture on machine learning.",
      "confidence": 0.95
    },
    {
      "id": 1,
      "start": 5.2,
      "end": 12.8,
      "text": "We'll be covering neural networks and deep learning.",
      "confidence": 0.92
    }
  ],
  "language": "en",
  "duration": 3600.5
}
```

**Minimum Required Response:**
```json
{
  "text": "Full transcript text",
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Transcript segment text"
    }
  ]
}
```

**Error Response (HTTP 500):**
```json
{
  "error": "Error message describing what went wrong"
}
```

---

## Functional Requirements

### 1. Audio Extraction
- Extract audio track from video file
- Handle various audio codecs and formats
- Convert to format suitable for Whisper (WAV, MP3)

### 2. Speech-to-Text Transcription
- Use Whisper model (OpenAI Whisper or similar)
- Generate accurate transcriptions
- Support multiple languages (auto-detect or specify)
- Handle different audio qualities and background noise

### 3. Timestamp Alignment
- Provide word-level or segment-level timestamps
- Align transcript segments with video timeline
- Include start and end times for each segment

### 4. Output Generation
- Return structured JSON response
- Include full transcript text
- Include segmented transcript with timestamps
- Optionally include confidence scores

---

## Technical Requirements

### Performance
- Process audio efficiently (consider GPU acceleration)
- Handle videos up to 500MB
- Complete processing within reasonable time (backend timeout: 300 seconds)
- Optimize for long-form content (lectures can be 30+ minutes)

### Model Selection
- Use appropriate Whisper model size:
  - `tiny`, `base`, `small` - Faster, less accurate
  - `medium`, `large` - Slower, more accurate
- Consider `large-v2` or `large-v3` for best accuracy

### Error Handling
- Handle invalid video formats gracefully
- Handle videos without audio track
- Return clear error messages on failure
- Handle corrupted or unreadable video files

### Response Time
- Backend timeout: 300 seconds (5 minutes)
- Aim for faster processing when possible
- Consider chunking very long videos

---

## Implementation Guidelines

### Recommended Libraries
- **Whisper**: OpenAI Whisper (whisper library)
- **Audio Processing**: ffmpeg-python, pydub, librosa
- **Video Processing**: OpenCV (cv2), moviepy
- **Web Framework**: FastAPI (recommended) or Flask
- **Deployment**: Google Colab + ngrok (for development)

### Example FastAPI Structure
```python
from fastapi import FastAPI, File, UploadFile, Form
import whisper
import json

app = FastAPI()

# Load Whisper model once at startup
model = whisper.load_model("base")

@app.post("/transcribe")
async def transcribe_video(
    video: UploadFile = File(...),
    job_id: str = Form(...)
):
    # 1. Extract audio from video
    # 2. Load audio into Whisper
    # 3. Run transcription
    # 4. Format results with timestamps
    # 5. Return JSON
    result = model.transcribe(audio_path)
    
    return {
        "text": result["text"],
        "segments": result["segments"],
        "language": result["language"]
    }
```

### Whisper Model Loading
```python
import whisper

# Load model (do this once, not per request)
model = whisper.load_model("base")  # or "small", "medium", "large"

# Transcribe audio
result = model.transcribe("audio.wav")

# Result structure:
# {
#   "text": "full transcript",
#   "segments": [
#     {
#       "id": 0,
#       "seek": 0,
#       "start": 0.0,
#       "end": 5.2,
#       "text": "segment text",
#       "tokens": [...],
#       "temperature": 0.0,
#       "avg_logprob": -0.5,
#       "compression_ratio": 2.0,
#       "no_speech_prob": 0.1
#     }
#   ],
#   "language": "en"
# }
```

---

## Integration with Backend

### How Backend Calls Whisper Service
1. Backend receives video upload
2. Backend creates job entry in database
3. Backend calls: `POST {WHISPER_SERVICE_URL}/transcribe`
   - Sends video file and job_id
4. Backend waits for response (up to 300 seconds)
5. Backend saves response to `storage/job_{id}/transcript.json`
6. Backend updates job status to `done` or `failed`

### Parallel Processing
- OCR and Whisper services run **in parallel** (simultaneously)
- Both must complete before LLM service is triggered
- Backend waits for both to finish

### Backend Configuration
- Set `WHISPER_SERVICE_URL` in `.env` file
- Example: `WHISPER_SERVICE_URL=https://your-ngrok-url.ngrok-free.dev`

---

## Response Format Details

### Required Fields
- `text` (string) - Full transcript text
- `segments` (array) - Array of transcript segments with timestamps

### Segment Structure
Each segment should have:
- `start` (float) - Start time in seconds
- `end` (float) - End time in seconds
- `text` (string) - Transcript text for this segment

### Optional Fields
- `language` (string) - Detected language code (e.g., "en", "es")
- `duration` (float) - Total audio duration in seconds
- `confidence` (float) - Confidence score (0.0 to 1.0)

---

## Testing Checklist

- [ ] Service accepts video file upload
- [ ] Service extracts audio from video
- [ ] Service generates accurate transcriptions
- [ ] Service returns timestamps for segments
- [ ] Service handles different video formats
- [ ] Service handles videos without audio
- [ ] Service handles errors gracefully
- [ ] Service completes within timeout period
- [ ] Service works with ngrok tunnel
- [ ] Response format matches expected structure

---

## Example Test Request

```python
import requests

# Test with sample video
url = "https://your-ngrok-url.ngrok-free.dev/transcribe"
files = {'video': open('test_video.mp4', 'rb')}
data = {'job_id': 'test_123'}

response = requests.post(url, files=files, data=data)
print(response.status_code)
print(response.json())
```

---

## Notes for Implementation

1. **Audio Extraction**: Use ffmpeg or similar to extract audio track
2. **Model Size**: Balance between accuracy and speed (start with "base" or "small")
3. **GPU Usage**: Use GPU if available for faster processing
4. **Chunking**: For very long videos, consider chunking and merging results
5. **Language Detection**: Whisper auto-detects language, but you can specify
6. **Error Messages**: Provide clear error messages for debugging
7. **Logging**: Log processing progress for debugging
8. **Resource Management**: Clean up temporary files after processing

---

## Whisper Installation

```bash
pip install openai-whisper
pip install ffmpeg-python  # For audio extraction
```

Or in Colab:
```python
!pip install openai-whisper
!apt-get install ffmpeg
```

---

## Example Complete Implementation

```python
from fastapi import FastAPI, File, UploadFile, Form
import whisper
import subprocess
import os
import json

app = FastAPI()

# Load model once
model = whisper.load_model("base")

@app.post("/transcribe")
async def transcribe_video(
    video: UploadFile = File(...),
    job_id: str = Form(...)
):
    try:
        # Save video temporarily
        video_path = f"/tmp/{job_id}_video.mp4"
        with open(video_path, "wb") as f:
            f.write(await video.read())
        
        # Extract audio
        audio_path = f"/tmp/{job_id}_audio.wav"
        subprocess.run([
            "ffmpeg", "-i", video_path, 
            "-vn", "-acodec", "pcm_s16le", 
            "-ar", "16000", "-ac", "1", 
            audio_path
        ], check=True)
        
        # Transcribe
        result = model.transcribe(audio_path)
        
        # Format response
        response = {
            "text": result["text"],
            "segments": [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"]
                }
                for seg in result["segments"]
            ],
            "language": result["language"]
        }
        
        # Cleanup
        os.remove(video_path)
        os.remove(audio_path)
        
        return response
        
    except Exception as e:
        return {"error": str(e)}, 500
```

---

## Contact
For questions about integration, refer to the backend developer (Person 4 - System Architect).
