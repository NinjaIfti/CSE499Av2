# OCR Service Requirements

## Overview
The OCR service extracts text from board and slide content in lecture videos. This service is called by the Flask backend after a video is uploaded.

---

## API Endpoint Specification

### Endpoint Details
- **URL Path**: `/process`
- **HTTP Method**: `POST`
- **Content-Type**: `multipart/form-data`

### Request Format

**Form Fields:**
- `video` (file, required) - Video file to process
  - Supported formats: MP4, AVI, MOV, MKV, WebM
  - Maximum size: 500MB (handled by backend)
- `job_id` (string, required) - Job identifier from backend

**Example Request:**
```python
import requests

files = {'video': open('lecture.mp4', 'rb')}
data = {'job_id': '123'}
response = requests.post('https://your-ngrok-url/process', files=files, data=data)
```

### Response Format

**Success Response (HTTP 200):**
```json
{
  "text": "Complete extracted text from all frames",
  "frames": [
    {
      "frame_number": 0,
      "timestamp": 0.0,
      "text": "Text extracted from this frame",
      "confidence": 0.95
    },
    {
      "frame_number": 30,
      "timestamp": 1.0,
      "text": "Text from frame at 1 second",
      "confidence": 0.92
    }
  ],
  "summary": "Brief summary of extracted content",
  "total_frames_processed": 150
}
```

**Minimum Required Response:**
```json
{
  "text": "All extracted text combined"
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

### 1. Video Processing
- Accept video files in common formats (MP4, AVI, MOV, MKV, WebM)
- Extract frames from video (sample every N seconds or detect key frames)
- Process frames to detect text regions (boards, slides, whiteboards)

### 2. Text Extraction
- Use OCR engine (e.g., Tesseract, EasyOCR, PaddleOCR, or cloud APIs)
- Extract text from detected regions
- Combine text from all frames into a single output
- Handle different text orientations and sizes

### 3. Frame Filtering (Recommended)
- Skip duplicate frames (similar content)
- Focus on frames with significant text content
- Filter out frames with no readable text

### 4. Output Generation
- Return structured JSON response
- Include extracted text as main field
- Optionally include frame-level details with timestamps
- Include confidence scores if available

---

## Technical Requirements

### Performance
- Process videos efficiently (consider GPU acceleration)
- Handle videos up to 500MB
- Complete processing within reasonable time (backend timeout: 300 seconds)

### Error Handling
- Handle invalid video formats gracefully
- Return clear error messages on failure
- Handle corrupted or unreadable video files

### Response Time
- Backend timeout: 300 seconds (5 minutes)
- Aim for faster processing when possible
- Consider async processing for very long videos

---

## Implementation Guidelines

### Recommended Libraries
- **OCR Engines**: Tesseract OCR, EasyOCR, PaddleOCR, Google Cloud Vision API
- **Video Processing**: OpenCV (cv2), ffmpeg-python, imageio
- **Web Framework**: FastAPI (recommended) or Flask
- **Deployment**: Google Colab + ngrok (for development)

### Example FastAPI Structure
```python
from fastapi import FastAPI, File, UploadFile, Form
from typing import Optional
import json

app = FastAPI()

@app.post("/process")
async def process_video(
    video: UploadFile = File(...),
    job_id: str = Form(...)
):
    # 1. Save video temporarily
    # 2. Extract frames
    # 3. Run OCR on frames
    # 4. Combine results
    # 5. Return JSON
    return {
        "text": "extracted text",
        "frames": [...]
    }
```

---

## Integration with Backend

### How Backend Calls OCR Service
1. Backend receives video upload
2. Backend creates job entry in database
3. Backend calls: `POST {OCR_SERVICE_URL}/process`
   - Sends video file and job_id
4. Backend waits for response (up to 300 seconds)
5. Backend saves response to `storage/job_{id}/ocr_output.json`
6. Backend updates job status to `done` or `failed`

### Backend Configuration
- Set `OCR_SERVICE_URL` in `.env` file
- Example: `OCR_SERVICE_URL=https://your-ngrok-url.ngrok-free.dev`

---

## Testing Checklist

- [ ] Service accepts video file upload
- [ ] Service extracts text from video frames
- [ ] Service returns valid JSON response
- [ ] Service handles different video formats
- [ ] Service handles errors gracefully
- [ ] Service completes within timeout period
- [ ] Service works with ngrok tunnel
- [ ] Response format matches expected structure

---

## Example Test Request

```python
import requests

# Test with sample video
url = "https://your-ngrok-url.ngrok-free.dev/process"
files = {'video': open('test_video.mp4', 'rb')}
data = {'job_id': 'test_123'}

response = requests.post(url, files=files, data=data)
print(response.status_code)
print(response.json())
```

---

## Notes for Implementation

1. **Frame Sampling**: Don't process every frame - sample every 1-2 seconds or detect scene changes
2. **Text Aggregation**: Combine text from multiple frames intelligently (avoid duplicates)
3. **Error Messages**: Provide clear error messages for debugging
4. **Logging**: Log processing progress for debugging
5. **Resource Management**: Clean up temporary files after processing

---

## Contact
For questions about integration, refer to the backend developer (Person 4 - System Architect).
