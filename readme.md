
# 📚 Distributed Multimodal Lecture Intelligence System

## 🚀 Overview

This project is a **Distributed AI-Powered Lecture Intelligence Platform** designed to automatically process uploaded lecture videos using multimodal AI pipelines.

The system integrates:

* 🎥 OCR for board & slide text extraction
* 🎙️ Speech-to-text transcription (Whisper)
* 🧠 LLM-based knowledge structuring
* 💬 Interactive lecture chat assistant
* 📊 Unified dashboard with persistent storage

The goal is to transform raw lecture videos into structured, searchable, and interactive learning content.

---

# 🏗️ System Architecture

The platform follows a **distributed microservice architecture**:

```
User
  ↓
Unified Dashboard (Flask Backend)
  ↓
Orchestrator
  ↓
OCR Service (Colab + ngrok)
Whisper Service (Colab + ngrok)
  ↓
LLM Service (Colab + ngrok)
  ↓
Structured Notes + Chat System
```

Each AI module runs independently and communicates through REST APIs.
Persistent state and automation logic are managed centrally.

---

# 👥 Team Role Distribution

## 👤 Person 1 — Vision Processing Engineer

* Extract board and slide content using OCR
* Image preprocessing and frame filtering
* Structured JSON output generation

---

## 👤 Person 2 — Audio Intelligence Engineer

* Extract audio from video
* Perform speech-to-text transcription
* Maintain timestamp alignment
* Generate structured transcript output

---

## 👤 Person 3 — LLM & Knowledge Structuring Engineer

* Merge OCR + transcript outputs
* Generate structured lecture notes
* Create summaries, key points, equations
* Implement context-aware lecture chat logic

---

## 👤 Person 4 — System Architect & Backend Engineer (My Role)

I am responsible for:

* Designing and implementing the unified dashboard
* Backend development using Flask
* SQLite database design and management
* Persistent storage architecture
* Orchestration of distributed AI services
* API communication with OCR, Whisper, and LLM services
* Automated job tracking and workflow control
* Chat system integration
* Failure handling and service coordination

I built the **core orchestration layer** that connects all AI modules into one fully automated platform.

---

# 🗄️ Database Design (SQLite)

The system stores metadata in SQLite.

### Tables:

### Users

* id
* name
* email
* password_hash
* created_at

### Jobs

* id
* user_id
* video_path
* ocr_status
* whisper_status
* llm_status
* final_status
* created_at

### Lectures

* id
* job_id
* summary
* notes_path
* transcript_path

### Chats

* id
* lecture_id
* user_id
* question
* answer
* created_at

---

# 💾 Storage Structure

Each job creates a structured directory:

```
/storage
    /job_<id>/
        video.mp4
        ocr_output.json
        transcript.json
        final_notes.json
```

This ensures:

* Clean separation
* Persistent storage
* Easy debugging
* Scalable design

---

# ⚙️ Automated Workflow

1. User uploads a lecture video.
2. A job entry is created in the database.
3. OCR and Whisper services are triggered in parallel.
4. Once both complete, the LLM service is triggered.
5. Structured lecture notes are generated.
6. User can interact with the lecture via chat.

All processes are automated through the orchestration layer.

---

# 💬 Interactive Lecture Chat

The chat module enables:

* Context-aware Q&A
* Follow-up explanations
* Lecture-grounded responses
* Conversation memory per lecture

This transforms static lecture extraction into an interactive learning assistant.

---

# 🔬 Research Contribution

This system demonstrates:

* Distributed GPU-backed AI microservices
* Multimodal content fusion
* Automated orchestration framework
* Persistent state management
* Interactive pedagogical AI agent

---

# 🚀 Future Improvements

* Replace ngrok with production cloud deployment
* Add job queue system (Celery or similar)
* Implement vector-based retrieval (RAG enhancement)
* Deploy scalable cloud infrastructure
* Add performance monitoring and logging

---

# 🏁 Conclusion

This project goes beyond simple transcription by building a fully automated, distributed lecture intelligence system with structured knowledge generation and interactive AI tutoring capabilities.

